import time
import easyocr
import tkinter as tk
from tkinter import messagebox
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import NoSuchElementException
from enum import Enum

class SeatType(Enum):
    TABLE_SEAT = 1
    VIP_SEAT = 2
    R_SEAT = 3
    S_SEAT = 4
    A_SEAT = 5

def launch_browser():
    # 브라우저 꺼짐 방지 옵션
    chrome_options = Options()
    chrome_options.add_experimental_option("detach", True)

    # 크롬 드라이버 생성
    driver = webdriver.Chrome(options=chrome_options)
    return driver


def login(driver, id, password):
    # 페이지 로딩이 완료될 때 까지 기다리는 코드
    driver.implicitly_wait(3)

    # 사이트 접속하기
    driver.get(url='https://ticket.interpark.com/Gate/TPLogin.asp')

    # 에러 수정
    # 필요한 정보들이 Iframe에 존재(전체 Frame과는 별개)
    # driver를 Iframe으로 교체
    iframes = driver.find_elements(By.TAG_NAME, "iframe")
    driver.switch_to.frame(iframes[0])

    # id 입력
    id_input = driver.find_element(By.CSS_SELECTOR, '#userId')
    id_input.send_keys(id)
    time.sleep(1)
    # pw 입력
    pw_input = driver.find_element(By.CSS_SELECTOR, '#userPwd')
    pw_input.send_keys(password)
    time.sleep(1)
    # button 클릭
    button = driver.find_element(By.CSS_SELECTOR, '#btn_login')
    button.click()
    time.sleep(1)


def access_performance_page(driver, my_Url):
    driver.get(my_Url)
    time.sleep(0.3)

    button = driver.find_element(By.XPATH, "//*[@id='popup-prdGuide']/div/div[3]/button")
    button.click()
    time.sleep(1)


def select_date(driver, my_WantDay):
    find_day = driver.find_element(By.XPATH, "//li[text()='" + str(my_WantDay) + "']")
    find_day.click()


def proceed_to_reservation(driver):
    # 예매하기 버튼 클릭
    go_button = driver.find_element(By.CSS_SELECTOR, "a.sideBtn.is-primary")
    go_button.click()

    # 최대 10초간 팝업 창이 나타날 때까지 대기
    wait = WebDriverWait(driver, 10)
    wait.until(EC.number_of_windows_to_be(2))  # 예상하는 창의 개수를 설정합니다. 이 경우에는 2개의 창이 되어야 합니다.

    # 모든 창 핸들을 가져옵니다.
    window_handles = driver.window_handles

    # 현재 창의 핸들을 가져옵니다.
    current_window_handle = driver.current_window_handle
    print(driver.current_window_handle)

    # 새로 열린 창 핸들을 찾습니다.
    new_window_handle = None
    for handle in window_handles:
        if handle != current_window_handle:
            new_window_handle = handle
            break

    # 새로 열린 창으로 이동합니다.
    if new_window_handle:
        driver.switch_to.window(new_window_handle)
    else:
        print("새로운 창이 열리지 않았습니다.")


#좌석 탐색 및 선택
def select_seat(driver, seat_type, start_li_num=1, search_count=0):
    print(driver.window_handles)
    print(driver.current_window_handle)
    driver.switch_to.window(driver.window_handles[-1])
    driver.switch_to.frame(driver.find_element(By.XPATH, '//*[@id="ifrmSeat"]'))

    # 좌석등급 선택
    seat_xpath = {
        SeatType.TABLE_SEAT: '//*[@id="GradeRow"][2]/td[1]/div/span[2]',
        SeatType.VIP_SEAT: '//*[@id="GradeRow"][3]/td[1]/div/span[2]',
        SeatType.R_SEAT: '//*[@id="GradeRow"][4]/td[1]/div/span[2]',
        SeatType.S_SEAT: '//*[@id="GradeRow"][5]/td[1]/div/span[2]',
        SeatType.A_SEAT: '//*[@id="GradeRow"][6]/td[1]/div/span[2]'
    }
    seat_xpath_value = seat_xpath.get(seat_type)
    if seat_xpath_value:
        driver.find_element(By.XPATH, seat_xpath_value).click()
    else:
        print("Invalid seat type")

    li_elements = driver.find_elements(By.XPATH, '//*[@id="GradeDetail"]/div/ul/li')
    li_maxcount = len(li_elements)
    li_num = start_li_num
    
    while True:
        # 0석이 아닌 좌석 우선 탐색
        elements = driver.find_elements(By.XPATH, '//*[@id="GradeDetail"]/div/ul/li')
        for idx, element in enumerate(elements, start=1):
            text = element.text
            if "0석" not in text:
                print(f'{idx}번째 좌석은 0석 아니다.')
                li_num = idx
                search_count += 1
                if search_count >= 5:  # 5번째 검색 시 새로고침
                    driver.refresh()  # 브라우저 새로고침
                    select_seat(driver, seat_type, li_num, 0)  # 다시 시작
                    return
                
        # 세부 구역 선택
        if li_num > li_maxcount:
            li_num = 1

        driver.find_element(By.XPATH, f'//*[@id="GradeDetail"]/div/ul/li[{li_num}]/a').click()

        # 좌석선택 아이프레임으로 이동
        driver.switch_to.frame(driver.find_element(By.XPATH, '//*[@id="ifrmSeatDetail"]'))

        # 좌석이 있으면 좌석 선택
        try:
            driver.find_element(By.XPATH, '//*[@id="Seats"]').click()
            # 결제 함수 실행
            payment(driver)
            print('select payment')
            break

        # 좌석이 없으면 다시 조회
        except:
            print(f'******{li_num}번째 영역에는 자리가 없습니당. 다시 선택합니다*******')
            li_num = li_num + 1
            driver.switch_to.default_content()
            driver.switch_to.frame(driver.find_element(By.XPATH, '//*[@id="ifrmSeat"]'))
            driver.find_element(By.XPATH, '/html/body/form[1]/div/div[1]/div[3]/div/p/a/img').click()
            time.sleep(0.5)           

            if li_num % 2 == 0:  # li_num이 2의 배수인 경우
                driver.refresh()  # 브라우저 새로고침
                print(f'******새로고침*******')
                select_seat(driver, seat_type, li_num)
                break


# 팝업창 표시 함수
def show_popup():
    root = tk.Tk()
    root.withdraw()  # 윈도우 창을 표시하지 않음
    messagebox.showinfo("결제해주세요!!", "자리를 성공적으로 잡았습니다 후딱 결제해주세요!!")
    root.mainloop()

# 결제
def payment(driver):
    # 좌석선택 완료 버튼 클릭
    driver.switch_to.default_content()
    driver.switch_to.frame(driver.find_element(By.XPATH, '//*[@id="ifrmSeat"]'))
    driver.find_element(By.XPATH, '//*[@id="NextStepImage"]').click()

    # 가격선택
    driver.switch_to.default_content()
    driver.switch_to.frame(driver.find_element(By.XPATH, "//*[@id='ifrmBookStep']"))
    select = Select(driver.find_element(By.XPATH, '//*[@id="PriceRow001"]/td[3]/select'))
    select.select_by_index(1)
    driver.switch_to.default_content()
    driver.find_element(By.XPATH, '//*[@id="SmallNextBtnImage"]').click()

    # 예매자 확인
    driver.switch_to.frame(driver.find_element(By.XPATH, "//*[@id='ifrmBookStep']"))
    driver.find_element(By.XPATH, '//*[@id="YYMMDD"]').send_keys('951207')
    driver.switch_to.default_content()
    driver.find_element(By.XPATH, '//*[@id="SmallNextBtnImage"]').click()

    # 예약 완료 메시지 표시
    show_popup()

    while True:
        time.sleep(3600)  # 2시간 동안 대기

    # # 결제방식 선택
    # driver.switch_to.frame(driver.find_element(By.XPATH, '//*[@id="ifrmBookStep"]'))
    # driver.find_element(By.XPATH, '//*[@id="Payment_22004"]/td/input').click()

    # select2 = Select(driver.find_element(By.XPATH, '//*[@id="BankCode"]'))
    # select2.select_by_index(1)
    # driver.switch_to.default_content()
    # driver.find_element(By.XPATH, '//*[@id="SmallNextBtnImage"]').click()

    # # 동의 후, 결제하기
    # driver.switch_to.frame(driver.find_element(By.XPATH, '//*[@id="ifrmBookStep"]'))
    # driver.find_element(By.XPATH, '//*[@id="checkAll"]').click()
    # driver.switch_to.default_content()
    # driver.find_element(By.XPATH, '//*[@id="LargeNextBtnImage"]').click()

# 보안문제 해제
def ocr_captcha(driver, my_SeatType):
    # 현재 창을 인터파크 페이지로 전환
    driver.switch_to.window(driver.window_handles[1])
    
    # iframe으로 이동
    while True:
        try:
            # iframe으로 이동
            driver.switch_to.frame(driver.find_element(By.XPATH, "//*[@id='ifrmSeat']"))
            break  # 프레임을 찾으면 반복문 종료
        except NoSuchElementException:
            print("이미지가 없어서 재검색중입니다....")
            time.sleep(3)  # 3초 대기 후 다시 시도


    # 이미지 캡쳐 후 인증
    while True:
            # 입력해야될 문자 이미지가 나타날 때까지 대기
            capchaPng = WebDriverWait(driver, 10).until(
                EC.visibility_of_element_located((By.XPATH, "//*[@id='imgCaptcha']")))

            # easyocr 이미지내 인식할 언어 지정
            reader = easyocr.Reader(['en'])

            # 캡쳐한 이미지에서 문자열 인식하기
            result = reader.readtext(capchaPng.screenshot_as_png, detail=0)

            # 이미지에 점과 직선이 포함되어있어서 문자 인식이 완벽하지 않아서 데이터를 수동으로 보정해주기로 했습니다.
            capchaValue = result[0].replace(' ', '').replace('5', 'S').replace('0', 'O').replace('$', 'S').replace(',', '')\
                .replace(':', '').replace('.', '').replace('+', 'T').replace("'", '').replace('`', '')\
                .replace('1', 'L').replace('e', 'Q').replace('3', 'S').replace('€', 'C').replace('{', '').replace('-', '')

            # 입력할 텍스트박스 클릭하기.
            element = driver.find_element(By.XPATH, "//*[@id='divRecaptcha']/div[1]/div[3]")
            # 요소를 클릭합니다.
            element.click()
            
            # 추출된 문자열 텍스트박스에 입력하기.
            chapchaText = driver.find_element(By.XPATH, '//*[@id="txtCaptcha"]')
            chapchaText.send_keys(capchaValue)
            chapchaText.send_keys(Keys.ENTER)
            
            # 캡차 요소가 존재하는지 확인
            captcha_element = driver.find_element(By.XPATH, '//*[@id="divRecaptcha"]')

            # 캡차 요소가 화면에 표시되는지 확인
            if captcha_element.is_disStartTicketingMacroed():
                # 캡차 입력이 실패했을 때, 다시 시도
                print('Captcha entered incorrectly, retrying...')
                driver.find_element(By.XPATH, '//*[@id="divRecaptcha"]/div[1]/div[1]/a[1]').click()
            else:
                # 캡차 입력이 성공했을 때
                print('Captcha entered successfully')
                select_seat(driver, my_SeatType)
                break

def StartTicketingMacro():

    #티켓팅 할 링크 좌표
    my_Url = "https://tickets.interpark.com/goods/24005132"  
    #아이디
    my_Id = "아이디를 입력하는 곳"
    #비밀번호
    my_PassWord = "비밀번호를 입력하는 곳"  
    #좌석
    my_SeatType = SeatType.R_SEAT
    #날짜
    my_WantDay = 25

    #로그인
    driver = launch_browser()

    login(driver, my_Id, my_PassWord)       #로그인
    access_performance_page(driver, my_Url) #페이지 오류 나가기
    select_date(driver, my_WantDay)         #날짜 선택
    proceed_to_reservation(driver)          #예약
    ocr_captcha(driver, my_SeatType)        #보안문자







#################################나중에######################################################

def Button_Click():
    id_text = id_entry.get()
    password_text = password_entry.get()
    performance_text = performance_value.get()
    birthday_text = birthday_entry.get()
    option_text = option_var.get()
    
    StartTicketingMacro()






def add_log(log_message):
    log_text.config(state=tk.NORMAL)  # 로그를 수정 가능한 상태로 변경
    log_text.insert(tk.END, log_message + "\n")
    log_text.config(state=tk.DISABLED)  # 로그를 읽기 전용으로 변경
    log_text.see(tk.END)  # 로그 창을 맨 아래로 스크롤
    with open("log.txt", "a") as log_file:
        log_file.write(log_message + "\n")

def create_label_entry(window, text, row):
    label = tk.Label(window, text=text, width=12, anchor="center")  # 가운데 정렬
    label.grid(row=row, column=0)
    entry = tk.Entry(window)
    entry.grid(row=row, column=1, columnspan=5, pady=5, sticky="ew")  # 텍스트 입력 상자를 가운데 정렬
    return entry

def create_button(window, text, row):
    button = tk.Button(window, text=text, command=Button_Click)
    button.grid(row=row, column=0, columnspan=6, pady=10)

def create_booking_window():
    # Tkinter 윈도우 생성
    window = tk.Tk()
    window.title("인터파크 예약 매크로")

    # 윈도우 크기 설정
    window.geometry("400x400")

    global birthday_entry, id_entry, password_entry, performance_value, option_var, log_text

    # 생년월일 입력
    birthday_entry = create_label_entry(window, "생년월일:", 0)

    # 아이디 입력
    id_entry = create_label_entry(window, "아이디:", 1)

    # 비밀번호 입력
    password_entry = create_label_entry(window, "비밀번호:", 2)

    # 상품명(공연번호) 입력
    performance_value = create_label_entry(window, "상품명(공연번호):", 3)

    # 선택지 추가
    option_var = tk.StringVar(value="")  # 초기화
    option_label = tk.Label(window, text="선택지:", width=12, anchor="center")  # 가운데 정렬
    option_label.grid(row=4, column=0)
    options = ["테이블석", "VIP석", "R석", "S석", "A석"]
    for i, option in enumerate(options):
        tk.Radiobutton(window, text=option, variable=option_var, value="").grid(row=4, column=i+1, padx=1)


    # 로그 표시를 위한 텍스트 상자 추가
    log_text = tk.Text(window, height=10, width=50, state=tk.DISABLED, bg="light gray")  # 읽기 전용으로 설정, 밝은 회색 배경
    log_text.grid(row=6, column=0, columnspan=6, pady=10)

    # 로그 파일을 열어 이전 로그를 로드
    try:
        with open("log.txt", "r") as log_file:
            log_text.insert(tk.END, log_file.read())
    except FileNotFoundError:
        pass

    # 버튼 추가
    create_button(window, "Send Keys", 5)

    # 윈도우 실행
    window.mainloop()

if __name__ == "__main__":
    StartTicketingMacro()
    #create_booking_window()



