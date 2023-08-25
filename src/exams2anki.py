import argparse
import html
import io
import json
import os
import pkgutil
import random
import re
import textwrap
import time

import genanki
from selenium import webdriver
from selenium.webdriver.common.by import By
from tqdm import tqdm


def parse_args():
    parser = argparse.ArgumentParser(prog='exams2anki',
                                     description='Convert ExamTopics pages to Anki decks!',
                                     formatter_class=argparse.RawDescriptionHelpFormatter,
                                     epilog=textwrap.dedent('''\
                                        additional information:
                                          To get exam details look for the url on examtopics.com/exams/<provider>/<exam>
                                          You MUST have Contributor Access to the exam!
                                        '''))
    parser.add_argument('--user', '-u', type=str, dest='username',
                        default=os.environ.get('EXAMTOPICS_USER'),
                        help='Your ExamTopics username or email (env: EXAMTOPICS_USER)')
    parser.add_argument('--pass', '-p', type=str, dest='password',
                        default=os.environ.get('EXAMTOPICS_PASS'),
                        help="Your ExamTopics password (env: EXAMTOPICS_PASS)")
    parser.add_argument('--provider', '-pr', type=str, dest='provider',
                        help="URL Exam provider (Ex: amazon)")
    parser.add_argument('--exam', '-e', type=str, dest='exam',
                        help="URL Exam name (Ex: aws-certified-cloud-practitioner)")
    parser.add_argument('--template', '-t', type=str, dest='template',
                        help="Template folder path (Ex: ~/template)")
    parser.add_argument('--edge', action='store_true', dest='edge',
                        help="Use this flag if you have issues with chromedriver")
    parser.add_argument('--debug', action='store_true', dest='debug',
                        help="Display automated browser")
    args = parser.parse_args()
    if not (args.username and args.password):
        exit(parser.print_usage())
    return args


def generate_anki_id():
    return random.randrange(1 << 30, 1 << 31)


def create_deck(name, description):
    return genanki.Deck(generate_anki_id(), name, description)


def create_model(template):
    return genanki.Model(
        generate_anki_id(),
        'ExamTopics',
        fields=[
            {'name': 'Question'},
            {'name': 'Options'},
            {'name': 'Answer'},
            {'name': 'Comments'},
        ],
        templates=[
            {
                'name': 'ExamTopics',
                'qfmt': template['front'],
                'afmt': template['back'],
            },
        ],
        css=template['style'])


def create_note(model, question, options, answer, comments, question_images, answer_images, media_files):
    question_images_html = "".join(f"<img src='{img_name}' />" for img_name in question_images)
    answer_images_html = "".join(f"<img src='{img_name}' />" for img_name in answer_images)

    question_with_images = f"{question}\n{question_images_html}"
    answer_with_images = f"{answer}\n{answer_images_html}"

    return genanki.Note(
        model=model,
        fields=[
            question_with_images,
            json.dumps([html.escape(option) for option in options]),
            answer_with_images,
            json.dumps([{'comment': html.escape(c['comment']), 'upvotes': c['upvotes']} for c in comments]),
        ],
        tags=["images"]
    )


def generate_deck(title, description, cards, template_path, images_folder):
    if template_path:
        template = get_deck_template_from_path(template_path)
    else:
        template = get_deck_template_from_resource()

    deck = create_deck(title, description)
    model = create_model(template)

    media_files = {}  # Dictionary to store media files

    for card in cards:
        question_images = card['question_images']
        answer_images = card['answer_images']

        all_images = question_images + answer_images

        for img_name in all_images:
            img_path = os.path.join(images_folder, img_name)
            media_files[img_name] = img_path

        note = create_note(model, card['question'], card['options'], card['answer'],
                           card['comments'], question_images, answer_images, media_files)
        deck.add_note(note)

    sanitized_title = re.sub(r'[\\/:*?"<>|]', '', title)
    package = genanki.Package(deck)

    for _, media_path in media_files.items():
        package.media_files.append(media_path)

    package.write_to_file(f'{sanitized_title}.apkg')


def get_deck_template_from_path(path):
    front = read_file(path, 'frontside.html')
    back = read_file(path, 'backside.html')
    style = read_file(path, 'style.css')
    return {'front': front, 'back': back, 'style': style}


def get_deck_template_from_resource():
    front = get_data('template/frontside.html')
    back = get_data('template/backside.html')
    style = get_data('template/style.css')
    return {'front': front, 'back': back, 'style': style}


def extract_discussions(card):
    comments = card.find_elements(By.CLASS_NAME, 'comment-body')
    contents = [comment.find_element(By.CLASS_NAME, 'comment-content').text for comment in comments]
    upvotes = [comment.find_element(By.CLASS_NAME, 'upvote-text').text for comment in comments]
    upvotes = [[int(d) for d in upvote.split(' ') if d.isdigit()][0] for upvote in upvotes]
    if len(comments) != len(contents) or len(contents) != len(upvotes):
        raise ValueError(
            'Expected same length for comments, contents and upvotes!')
    discussions = [{'comment': contents[i].replace('\n', '').strip(), 'upvotes': upvotes[i]}
                   for i in range(len(comments))]
    return sorted(discussions, key=lambda d: d['upvotes'], reverse=True)[:5]


def extract_images_from_element(element, images_folder, question_index, is_answer=False):
    images = []
    img_elements = element.find_elements(By.TAG_NAME, 'img')

    for img_index, img in enumerate(img_elements):
        img_src = img.get_attribute('src')
        img_extension = os.path.splitext(img_src)[1]

        if is_answer:
            img_name = f"answer_{question_index}_{img_index}{img_extension}"
        else:
            img_name = f"question_{question_index}_{img_index}{img_extension}"

        img_path = os.path.join(images_folder, img_name)

        if not os.path.exists(img_path):
            img.screenshot(img_path)

        images.append(img_name)

    return images


def extract_cards(driver, images_folder):
    cards = driver.find_elements(By.CLASS_NAME, 'exam-question-card')
    extracted_cards = []

    for question_index, card in enumerate(cards):
        question_element = card.find_element(By.CLASS_NAME, 'card-text')
        answer_element = card.find_element(By.CLASS_NAME, 'question-answer')

        question = question_element.text
        answer = answer_element.text

        question_images = extract_images_from_element(question_element, images_folder, question_index)
        answer_images = extract_images_from_element(answer_element, images_folder, question_index, is_answer=True)

        options = [option.text for option in card.find_elements(By.CLASS_NAME, 'multi-choice-item')]
        discussions = extract_discussions(card)

        extracted_cards.append({
            'question': question,
            'answer': answer,
            'options': options,
            'comments': discussions,
            'question_images': question_images,
            'answer_images': answer_images
        })

    return extracted_cards


def next_page(driver, url, page_info):
    if page_info['page'] < page_info['total']:
        driver.get(f'{url}/view/{page_info["page"] + 1}')


def get_page_info(driver):
    page_info = driver.find_element(By.CLASS_NAME, 'card-text').text
    digits = [int(d) for d in page_info.replace('-', ' ').split(' ') if d.isdigit()]
    if len(digits) < 1:
        raise ValueError('Failed to collect page information!')
    time.sleep(10)
    return {'page': digits[0], 'total': digits[1], 'size': digits[3] - digits[2] + 1, 'min_item': digits[2], 'max_item': digits[3], 'total_items': digits[4]}


def login(driver, username, password):
    username_input = driver.find_element(By.ID, 'etemail')
    password_input = driver.find_element(By.ID, 'etpass')
    login_button = driver.find_element(By.CLASS_NAME, 'login-button')
    username_input.clear()
    username_input.send_keys(username)
    password_input.clear()
    password_input.send_keys(password)
    login_button.click()


def set_session_settings(driver):
    driver.find_element(By.ID, 'answer-expose-checkbox').click()
    driver.find_element(By.ID, 'inline-discussions-checkbox').click()
    driver.find_element(By.CLASS_NAME, 'btn-primary').click()


def get_exam_title(provider, exam):
    exam = exam.replace('-', ' ')
    return 'ExamTopics::{}::{}'.format(provider.capitalize(), exam.title())


def get_exam_info(driver, url):
    driver.get(url)
    info = driver.find_element(By.CLASS_NAME, 'exam-intro-box').text
    return info


def get_edge_driver(args):
    edge_options = webdriver.EdgeOptions()
    if not args.debug:
        edge_options.add_argument('headless')
    return webdriver.Edge(options=edge_options)


def get_chrome_driver(args):
    chrome_options = webdriver.ChromeOptions()
    if not args.debug:
        chrome_options.add_argument('headless')
        chrome_options.add_argument('silent')
        chrome_options.add_experimental_option('excludeSwitches', ['enable-logging'])
    return webdriver.Chrome(options=chrome_options)


def get_data(path):
    return pkgutil.get_data('exams2anki', path).decode('utf-8')


def read_file(folder_path, file):
    full_path = os.path.join(folder_path, file)
    return io.open(full_path, 'r', encoding='utf8').read()


def main():
    args = parse_args()
    url = f'https://www.examtopics.com/exams/{args.provider}/{args.exam}'

    images_folder = os.path.join(os.getcwd(), 'images', args.provider, args.exam)
    os.makedirs(images_folder, exist_ok=True)  # Create the folder if it doesn't exist

    driver = None
    if args.edge:
        driver = get_edge_driver(args)
    else:
        driver = get_chrome_driver(args)

    driver.get(f'{url}/custom-view/')

    login(driver, args.username, args.password)
    set_session_settings(driver)

    cards = []
    page_info = get_page_info(driver)
    title = get_exam_title(args.provider, args.exam)

    pbar = tqdm(total=page_info["total_items"])
    while not page_info or page_info['page'] < page_info['total']:
        page_info = get_page_info(driver)
        cards = cards + extract_cards(driver, images_folder)  # Pass images_folder here
        next_page(driver, url, page_info)
        pbar.update(page_info["size"])

        time.sleep(1)

    pbar.close()

    info = get_exam_info(driver, url)
    driver.quit()

    generate_deck(title, info, cards, args.template, images_folder)  # Pass images_folder here


if __name__ == '__main__':
    main()
