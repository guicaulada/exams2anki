import os
import sys

from selenium import webdriver


def extract_discussions(card):
    comments = card.find_elements_by_class_name('comment-body')
    contents = [comment.find_element_by_class_name('comment-content').text for comment in comments]
    upvotes = [comment.find_element_by_class_name('upvote-text').text for comment in comments]
    upvotes = [[int(d) for d in upvote.split(' ') if d.isdigit()][0] for upvote in upvotes]
    if len(comments) != len(contents) or len(contents) != len(upvotes):
        raise ValueError(
            'Expected same length for comments, contents and upvotes!')
    discussions = [{'comment': contents[i], 'upvotes': upvotes[i]} for i in range(len(comments))]
    return sorted(discussions, key=lambda d: d['upvotes'], reverse=True)[:5]


def exract_cards(driver):
    cards = driver.find_elements_by_class_name('exam-question-card')
    questions = [
        card.find_element_by_class_name('card-text').text for card in cards]
    options = [[option.text for option in card.find_elements_by_class_name('multi-choice-item')] for card in cards]
    answers = [card.find_element_by_class_name('question-answer').text for card in cards]
    discussions = [extract_discussions(card) for card in cards]
    print(discussions)
    if len(questions) != len(options) or len(options) != len(answers) or len(answers) != len(discussions):
        raise ValueError(
            'Expected same length for questions, options, answers and discussions!')
    return [{
        'question': questions[i],
        'options': options[i],
        'answer': answers[i],
        'comments': discussions[i]} for i in range(len(questions))]


def next_page(driver):
    next_questions = driver.find_element_by_class_name('btn-success')
    next_questions.click()


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
    driver.find_element_by_id('printable-checkbox').click()
    driver.find_element_by_id('inline-discussions-checkbox').click()
    driver.find_element_by_class_name('btn-primary').click()


if __name__ == '__main__':
    EXAM_LOGIN = os.environ.get('EXAM_TOPICS_EMAIL', sys.argv[3] if len(sys.argv) > 3 else None)
    EXAM_PASS = os.environ.get('EXAM_TOPICS_PASSWORD', sys.argv[4] if len(sys.argv) > 4 else None)
    EXAM_PROVIDER = sys.argv[1] if len(sys.argv) > 1 else ''
    EXAM_NAME = sys.argv[2] if len(sys.argv) > 2 else ''
    EXAM_URL = f'https://www.examtopics.com/exams/{EXAM_PROVIDER}/{EXAM_NAME}/custom-view/'

    if not all([EXAM_PROVIDER, EXAM_NAME, EXAM_LOGIN, EXAM_PASS]):
        print('Usage: exams2anki.py <provider> <exam> <username> <password>')
        print('Example: exams2anki.py amazon aws-certified-cloud-practitioner username password')
        print('You can also set user email and password as environment variables EXAM_TOPICS_EMAIL and EXAM_TOPICS_PASSWORD')
        print('To get exam details look for the url on examtopics.com/exams - you MUST have Contributor Access to the exam!')
        exit()

    driver = webdriver.Chrome()
    driver.get(EXAM_URL)

    login(driver, EXAM_LOGIN, EXAM_PASS)
    set_session_settings(driver)

    cards = []
    page_info = None
    while not page_info or page_info['page'] < page_info['total']:
        page_info = get_page_info(driver)
        cards = cards + exract_cards(driver)
        next_page(driver)
