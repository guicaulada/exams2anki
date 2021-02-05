import json
import os
import random
import sys

import genanki
from selenium import webdriver


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


def create_note(model, question, options, answer, comments):
    return genanki.Note(
        model=model,
        fields=[
            question,
            json.dumps(options),
            answer,
            json.dumps(comments)])


def generate_deck(title, description, cards):
    template = get_deck_template()
    deck = create_deck(title, description)
    model = create_model(template)
    for card in cards:
        note = create_note(model, card['question'], card['options'], card['answer'], card['comments'])
        deck.add_note(note)
    genanki.Package(deck).write_to_file(f'{title}.apkg')


def get_deck_template():
    front_path = get_relative_path(r'templates\frontside.html')
    back_path = get_relative_path(r'templates\backside.html')
    style_path = get_relative_path(r'templates\style.css')
    front_file = open(front_path)
    front = front_file.read()
    front_file.close()
    backfile = open(back_path)
    back = backfile.read()
    backfile.close()
    stylefile = open(style_path)
    style = stylefile.read()
    stylefile.close()
    return {'front': front, 'back': back, 'style': style}


def extract_discussions(card):
    comments = card.find_elements_by_class_name('comment-body')
    contents = [comment.find_element_by_class_name('comment-content').text for comment in comments]
    upvotes = [comment.find_element_by_class_name('upvote-text').text for comment in comments]
    upvotes = [[int(d) for d in upvote.split(' ') if d.isdigit()][0] for upvote in upvotes]
    if len(comments) != len(contents) or len(contents) != len(upvotes):
        raise ValueError(
            'Expected same length for comments, contents and upvotes!')
    discussions = [{'comment': contents[i].replace('\n', '').strip(), 'upvotes': upvotes[i]}
                   for i in range(len(comments))]
    return sorted(discussions, key=lambda d: d['upvotes'], reverse=True)[:5]


def exract_cards(driver):
    cards = driver.find_elements_by_class_name('exam-question-card')
    questions = [
        card.find_element_by_class_name('card-text').text for card in cards]
    options = [[option.text for option in card.find_elements_by_class_name('multi-choice-item')] for card in cards]
    answers = [card.find_element_by_class_name('question-answer').text for card in cards]
    discussions = [extract_discussions(card) for card in cards]
    if len(questions) != len(options) or len(options) != len(answers) or len(answers) != len(discussions):
        raise ValueError(
            'Expected same length for questions, options, answers and discussions!')
    return [{
        'question': questions[i],
        'options': options[i],
        'answer': answers[i],
        'comments': discussions[i]} for i in range(len(questions))]


def next_page(driver, page_info):
    if page_info['page'] < page_info['total']:
        driver.get(f'{EXAM_URL}/view/{page_info["page"] + 1}')


def get_page_info(driver):
    page_info = driver.find_element_by_class_name('card-text').text
    digits = [int(d) for d in page_info.replace('-', ' ').split(' ') if d.isdigit()]
    if len(digits) < 5:
        raise ValueError('Failed to collect page information!')
    return {'page': digits[0], 'total': digits[1], 'min_item': digits[2], 'max_item': digits[3], 'total_items': digits[4]}


def login(driver, username, password):
    username_input = driver.find_element_by_class_name('username-text')
    password_input = driver.find_element_by_class_name('password-text')
    login_button = driver.find_element_by_class_name('login-button')
    username_input.clear()
    username_input.send_keys(username)
    password_input.clear()
    password_input.send_keys(password)
    login_button.click()


def set_session_settings(driver):
    driver.find_element_by_id('answer-expose-checkbox').click()
    driver.find_element_by_id('inline-discussions-checkbox').click()
    driver.find_element_by_class_name('btn-primary').click()


def get_exam_title(driver):
    title = driver.find_element_by_id('exam-box-title').text
    return title.replace('Exam Actual Questions', '').strip()


def get_exam_info(driver, url):
    driver.get(url)
    info = driver.find_element_by_class_name('exam-intro-box').text
    return info


def get_driver():
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument('headless')
    chrome_options.add_argument('silent')
    chrome_options.add_experimental_option('excludeSwitches', ['enable-logging'])
    return webdriver.Chrome(options=chrome_options)


def get_relative_path(path):
    script_dir = os.path.dirname(__file__)
    return os.path.join(script_dir, path)


if __name__ == '__main__':
    EXAM_LOGIN = os.environ.get('EXAM_TOPICS_EMAIL', sys.argv[3] if len(sys.argv) > 3 else None)
    EXAM_PASS = os.environ.get('EXAM_TOPICS_PASSWORD', sys.argv[4] if len(sys.argv) > 4 else None)
    EXAM_PROVIDER = sys.argv[1] if len(sys.argv) > 1 else ''
    EXAM_NAME = sys.argv[2] if len(sys.argv) > 2 else ''
    EXAM_URL = f'https://www.examtopics.com/exams/{EXAM_PROVIDER}/{EXAM_NAME}'

    if not all([EXAM_PROVIDER, EXAM_NAME, EXAM_LOGIN, EXAM_PASS]):
        print('Usage: exams2anki.py <provider> <exam> <username> <password>')
        print('Example: exams2anki.py amazon aws-certified-cloud-practitioner username password')
        print('You can also set username and password as environment variables EXAM_TOPICS_EMAIL and EXAM_TOPICS_PASSWORD')
        print('To get exam details look for the url on examtopics.com/exams - you MUST have Contributor Access to the exam!')
        exit()

    driver = get_driver()
    driver.get(f'{EXAM_URL}/custom-view/')

    login(driver, EXAM_LOGIN, EXAM_PASS)
    set_session_settings(driver)

    cards = []
    page_info = None
    title = get_exam_title(driver)
    while not page_info or page_info['page'] < page_info['total']:
        page_info = get_page_info(driver)
        cards = cards + exract_cards(driver)
        # next_page(driver, page_info)
        break

    info = get_exam_info(driver, EXAM_URL)
    driver.close()

    generate_deck(title, info, cards)
