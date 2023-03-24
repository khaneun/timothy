import os
import sys

from PyQt5.QAxContainer import *
from PyQt5.QtCore import *
from PyQt5.QtTest import *
from config.errorCode import *
from config.kiwoomType import *
from config.logger import *
from strategy.budget import *

class Kiwoom(QAxWidget):
    def __init__(self):
        super().__init__()

        ### Kiwoom Instance 생성
        self.get_ocx_instance()
        ############################

        ### Slot 생성
        self.event_slots()
        self.real_event_slots()
        ############################

        ### Logger 셍성
        self.logger = timothyLogger("Kiwoom")
        ############################

        ### Eventloop 모음
        self.login_event_loop       = QEventLoop() # Login 용
        self.transaction_event_loop = QEventLoop() # 키움 API Transaction 처리용
        self.analytics_event_loop   = QEventLoop() # 데이터 분석용
        ############################

        ### Constants
        self.budget = 0
        self.lower_excaped_period   = 5
        self.moving_average_period  = 20
        self.realType = RealType()
        ############################

        ### 변수 모음
        self.account_num = None
        self.calcul_data = []
        self.portfolio_stock_dict = {}
        self.jango_dict = {}

        ## 계좌관련 변수

        self.account_stock_dict = {}
        self.not_account_stock_dict = {}
        ############################

        ### Request Nickname
        self.request_deposit_received   = "예수금상세현황조회"
        self.request_evaluated_balance  = "계좌평가잔고내역요청"
        self.request_not_concluded      = "실시간미체결요청"
        self.inquiry_daily_boxplot      = "주식일봉차트조회"

        ### Screen Number 모음
        self.screen_start_stop_real     = "1000"
        self.screen_Numner              = "2000"
        self.screen_calculate_Numner    = "4000"
        self.screen_real_stock          = "5000" # 종목별로 할당할 스크린 번호
        self.screen_meme_stock          = "6000" # 종목별 할당할 주문용 스크린 번호
        ############################

        self.logger.info("자동 매매 프로그램 시작")

        self.login()
        self.get_account_info()
        self.detail_account_info()
        self.detail_account_mystock()
        self.not_concluded_account()
        #self.calculator_fnc()

        self.read_code() # 저장된 종목들 불러오기 (포트폴리오 구성)
        self.screen_number_setting() # 스크린 번호 할당

        # 실시간 시세를 등록하는 함수 : 등록? 어디에?
        # FID : Function ID 같음, 구분 번호
        self.dynamicCall("SetRealReg(QString, QString, QString, QString)", self.screen_start_stop_real, '', self.realType.REALTYPE['장시작시간']['장운영구분'], 0)

        for code in self.portfolio_stock_dict.keys():
            screen_num = self.portfolio_stock_dict[code]['스크린번호']
            fids = self.realType.REALTYPE['주식체결']['체결시간']

            self.dynamicCall("SetRealReg(QString, QString, QString, QString)", screen_num, code , fids, 1)
            print("[__init__] 실시간 등록 코드 : %s, 스크린번호 : %s, FID 번호 : %s" % (code, screen_num, fids))


    def get_ocx_instance(self):
        ### QAxWidget 내 Kiwoom API를 쓸 수 있도록 Control 추가
        self.setControl("KHOPENAPI.KHOpenAPICtrl.1")


    ### Slot만 모아놓은 Function
    def login_slot(self, errCode):
        self.logger.info("로그인 상태 [%s] "%errors(errCode))
        ### login 완료 후, Eventloop 종료
        self.login_event_loop.exit()
    def event_slots(self):
        self.OnEventConnect.connect(self.login_slot)
        self.OnReceiveTrData.connect(self.trdata_slot)
        self.OnReceiveMsg.connect(self.msg_slot)
    def real_event_slots(self):
        self.OnReceiveRealData.connect(self.realdata_slot)
        self.OnReceiveChejanData.connect(self.chejan_slot)


    ### Request만 모아놓은 Function
    def login(self):
        self.dynamicCall("CommConnect()")

        ### Login 완료될 때까지 대기
        self.login_event_loop.exec_()

    import logging
    def get_account_info(self):
        account_list = self.dynamicCall("GetLoginInfo(String)", "ACCNO")
        self.account_num = account_list.split(";")[0] # 8044716511 모의계좌번호
        self.logger.info("보유 계좌 번호 %s" % self.account_num)

    def detail_account_info(self):
        self.logger.info("%s 요청 [%s]" % (self.request_deposit_received, "opw00001"))
        self.dynamicCall("SetInputValue(String, String)", "계좌번호", self.account_num)
        self.dynamicCall("SetInputValue(String, String)", "비밀번호", "0000")
        self.dynamicCall("SetInputValue(String, String)", "비밀번호입력매체구분", "00")
        self.dynamicCall("SetInputValue(String, String)", "조회구분", "2")
        self.dynamicCall("CommRqData(String, String, int, String)", self.request_deposit_received, "opw00001", "0", self.screen_Numner)

        ### Eventloop 내 Callback 또는 Queue에 작업이 생성된다.
        self.transaction_event_loop.exec_()

    def detail_account_mystock(self, sPrevNext="0"):
        self.logger.info("%s 요청 [%s]" % (self.request_evaluated_balance, "opw00018"))
        self.dynamicCall("SetInputValue(String, String)", "계좌번호", self.account_num)
        self.dynamicCall("SetInputValue(String, String)", "비밀번호", "0000")
        self.dynamicCall("SetInputValue(String, String)", "비밀번호입력매체구분", "00")
        self.dynamicCall("SetInputValue(String, String)", "조회구분", "2")
        self.dynamicCall("CommRqData(String, String, int, String)", self.request_evaluated_balance, "opw00018", sPrevNext, self.screen_Numner)

        self.transaction_event_loop.exec_()

    def not_concluded_account(self, sPrevNext="0"):
        self.logger.info("%s 요청 [%s]" % (self.request_not_concluded, "opt10075"))
        self.dynamicCall("SetInputValue(QString, QString)", "계좌번호", self.account_num)
        self.dynamicCall("SetInputValue(QString, QString)", "체결구분", "1")
        self.dynamicCall("SetInputValue(QString, QString)", "매매구분", "0")
        self.dynamicCall("CommRqData(String, String, int, String)", self.request_not_concluded, "opt10075", sPrevNext, self.screen_Numner)

    def trdata_slot(self, sScrNo, sRQName, sTrCode, sRecordName, sPrevNext):
        '''

        :param sScrNo: 스크린번호
        :param sRQName: 요청시 Nickname
        :param sTrCode: 요청 ID
        :param sRecordName: 사용하지 않음
        :param sPrevNext: 다음 페이지 유무
        :return:
        '''

        if sRQName == self.request_deposit_received:
            deposit                 = self.dynamicCall("GetCommData(String, String, int, String)", sTrCode, sRQName, 0, "예수금")
            withdrawable_deposit    = self.dynamicCall("GetCommData(String, String, int, String)", sTrCode, sRQName, 0, "출금가능금액")

            self.logger.info("예수금 : %s | 출금가능금액 : %s" % (format(int(deposit), ','), format(int(withdrawable_deposit), ',')))

            ### 매입 예산 설정
            self.budget = budget_for_single_portfolio(deposit)

            self.transaction_event_loop.exit()

        # 자동 매매시 불필요 정보
        if sRQName == self.request_evaluated_balance:
            total_buy_money = self.dynamicCall("GetCommData(String, String, int, String)", sTrCode, sRQName, 0, "총매입금액")
            total_buy_money_result = int(total_buy_money)

            total_profit_loss_rate = self.dynamicCall("GetCommData(String, String, int, String)", sTrCode, sRQName, 0, "총수익률(%)")
            total_profit_loss_rate_result = float(total_profit_loss_rate)

            self.logger.debug("총매입금액 %s" % format(total_buy_money_result,','))
            self.logger.debug("총수익률(%%) %s" % total_profit_loss_rate_result)

            rows = self.dynamicCall("GetRepeatCnt(QString, QString)", sTrCode, sRQName)
            cnt = 0
            for i in range(rows):
                ### 종목번호 앞자리 영문자 1자 붙어있음, 국가 코드 구분 용도
                code = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, i, "종목번호")
                code = code.strip()[1:]

                code_nm             = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, i, "종목명")
                stock_quantity      = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, i, "보유수량")
                buy_price           = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, i, "매입가")
                learn_rate          = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, i, "수익률(%)")
                current_price       = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, i, "현재가")
                total_chegual_price = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, i, "매입금액")
                possible_quantity   = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, i, "매매가능수량")

                if code in self.account_stock_dict:
                    pass
                else:
                    self.account_stock_dict.update({code:{}})

                code_nm = code_nm.strip()
                stock_quantity = int(stock_quantity.strip())
                buy_price = int(buy_price.strip())
                learn_rate = float(learn_rate.strip())
                current_price = int(current_price.strip())
                total_chegual_price = int(total_chegual_price.strip())
                possible_quantity = int(0 if possible_quantity.strip() == '' else possible_quantity.strip())

                self.account_stock_dict[code].update({"종목명": code_nm})
                self.account_stock_dict[code].update({"보유수량": stock_quantity})
                self.account_stock_dict[code].update({"매입가": buy_price})
                self.account_stock_dict[code].update({"수익률(%)": learn_rate})
                self.account_stock_dict[code].update({"현재가": current_price})
                self.account_stock_dict[code].update({"매입금액": total_chegual_price})
                self.account_stock_dict[code].update({"매매가능수량": possible_quantity})
                cnt += 1

            self.logger.debug("계좌에 가지고 있는 종목 %s" % cnt)
            self.logger.debug("보유 종목 정보 : %s" % self.account_stock_dict)

            if sPrevNext == "2":
                self.detail_account_mystock(sPrevNext="2")
            else:
                self.transaction_event_loop.exit()

        elif sRQName == self.request_not_concluded:
            rows = self.dynamicCall("GetRepeatCnt(QString, QString)", sTrCode, sRQName)
            cnt = 0

            for i in range(rows):
                ### 종목번호 앞자리 영문자 1자 붙어있음, 국가 코드 구분 용도
                code = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, i, "종목번호")
                #code = code.strip()[1:]

                code_nm             = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, i, "종목코드")
                order_no            = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, i, "주문번호")
                order_status        = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, i, "주문상태")
                order_quantity      = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, i, "주문수량")
                order_price         = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, i, "주문가격")
                order_gubun         = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, i, "주문구분")
                not_quantity        = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, i, "미체결수량")
                ok_quantity         = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, i, "체결량")

                code = code.strip()
                code_nm = code_nm.strip()
                order_no = int(order_no.strip())
                order_status = order_status.strip()
                order_quantity = int(order_quantity.strip())
                order_price = int(order_price.strip())
                order_gubun = order_gubun.strip().lstrip('+').lstrip('-')
                not_quantity = int(not_quantity.strip())
                ok_quantity = int(ok_quantity.strip())

                if order_no in self.not_account_stock_dict:
                    pass
                else:
                    self.not_account_stock_dict[order_no] = {}
                    
                order_detail = self.not_account_stock_dict[order_no]

                order_detail.update({"종목코드": code})
                order_detail.update({"종목명": code_nm})
                order_detail.update({"주문번호": order_no})
                order_detail.update({"주문상태": order_status})
                order_detail.update({"주문수량": order_quantity})
                order_detail.update({"주문가격": order_price})
                order_detail.update({"주문구분": order_gubun})
                order_detail.update({"미체결수량": not_quantity})
                order_detail.update({"체결량": ok_quantity})

                self.logger.info("미체결 종목 : %s" % self.not_account_stock_dict[order_no])

                self.transaction_event_loop.exit()

        if sRQName == self.inquiry_daily_boxplot:
            code = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, 0, "종목코드")
            code = code.strip()

            if sPrevNext == "0":
                self.logger.debug("%s 일봉데이터 요청" % code)

            cnt = self.dynamicCall("GetRepeatCnt(QString, QString)", sTrCode, sRQName)

            ### 한번 조회하면 600일치까지 일봉데이터를 받을 수 있다.
            for i in range(cnt):
                data = []
                current_price   = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, i, "현재가")
                value           = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, i, "거래량")
                trading_value   = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, i, "거래대금")
                date            = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, i, "일자")
                start_price     = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, i, "시가")
                high_price      = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, i, "고가")
                low_price       = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, i, "저가")

                ### GetCommDataEx와 형식을 맞춰주기 위해 앞뒤 데이터에 공백 추가
                data.append("")

                data.append(int(current_price.strip()))
                data.append(int(value.strip()))
                data.append(int(trading_value.strip()))
                data.append(date.strip())
                data.append(int(start_price.strip()))
                data.append(int(high_price.strip()))
                data.append(int(low_price.strip()))

                data.append("")

                self.calcul_data.append(data.copy())

            # print(self.calcul_data)

            if sPrevNext == "2":
                self.day_kiwoom_db(code=code, sPrevNext=sPrevNext)
            else:
                # 참고 : https://futurestrade.tistory.com/89
                self.logger.debug("데이터 분석 : [%s]일 이동평균선 기준 가격 상승의 법칙 (ref. J.E.Granville 8법칙 중 4법칙)" % self.moving_average_period)
                self.logger.debug("[%s] 금일 기준 총 일봉 데이터 정보 갯수 : %s"%(code, len(self.calcul_data)))

                pass_success = False

                # 120일 이평선을 그릴만큼의 데이터가 있는지 체크
                if self.calcul_data == None or len(self.calcul_data) < self.moving_average_period:
                    pass_success = False
                else:
                    total_price = 0
                    # print("[trdata_slot|주식일봉차트조회] 120일 이동평균값 계산")
                    temp = self.calcul_data[:int(self.moving_average_period)]

                    for value in temp:
                        total_price += value[1]

                    moving_average_price = total_price / int(self.moving_average_period)

                    # print("[trdata_slot|주식일봉차트조회]  오늘자 주가가 120일 이평선에 걸쳐있는지 확인")
                    bottom_stock_price = False
                    check_price = None

                    # [6] : 고가 [7] : 저가
                    # print("[trdata_slot|주식일봉차트조회] 오늘 시가 : %s | 오늘 종가 : %s | 120 이평선 : %s" % (self.calcul_data[0][7], self.calcul_data[0][6], moving_average_price))
                    if int(self.calcul_data[0][7]) <= moving_average_price and moving_average_price <= int(self.calcul_data[0][6]):
                        # print("[trdata_slot|주식일봉차트조회] 오늘 주가 120이평선에 걸쳐있는 것 확인")
                        bottom_stock_price = True
                        check_price = int(self.calcul_data[0][6])

                    # 과거 일봉들이 120일 이평선보다 밑에 있는지 확인
                    # 그렇게 확인을 하다가 일봉이 120일 이평선보다 위에 있으면 계산 진행
                    prev_price = None
                    if bottom_stock_price == True:
                        moving_average_price_prev = 0
                        price_top_moving = False

                        idx = 1
                        while True:
                            if len(self.calcul_data[idx:]) < int(self.moving_average_period): # 120일치가 있는지 계속 확인
                                self.logger.debug("[%s] [%s]일치 데이터 없음"% (code, int(self.moving_average_period)))
                                break

                            total_price = 0
                            for value in self.calcul_data[idx:int(self.moving_average_period)+idx]:
                                total_price += int(value[1])
                            moving_average_price_prev = total_price / int(self.moving_average_period)

                            if moving_average_price_prev <= int(self.calcul_data[idx][6]) and idx <= int(self.lower_excaped_period):
                                # print("[trdata_slot|주식일봉차트조회] 20일 동안 주가가 120일 이평선과 같거나 이평선보다 위에 있으면 조건 통과 못함")
                                self.logger.info("Granville dead-cross priod : [%s]" % idx)
                                price_top_moving = False
                                break
                            elif int(self.calcul_data[idx][7]) > moving_average_price_prev and idx > int(self.lower_excaped_period):
                                # print("[trdata_slot|주식일봉차트조회] 120일 이평선 위에 있는 일봉 확인됨")
                                price_top_moving = True
                                prev_price = int(self.calcul_data[idx][7])

                            idx += 1

                        # 해당 부분 이평선이 가장 최근 일자의 이평선 가격보다 낮은지 확인
                        if price_top_moving == True:
                            if moving_average_price > moving_average_price_prev and check_price > prev_price:
                                # print("[trdata_slot|주식일봉차트조회] 포착된 이평선의 가격이 오늘자(최근일자) 이평선 가격보다 낮은 것 확인됨")
                                # print("[trdata_slot|주식일봉차트조회] 포착된 부분의 일봉 저가가 오늘자 고가보다 낮은 것으로 확인됨")
                                pass_success = True

                if pass_success == True:
                    self.logger.info("Granville target detected.")

                    code_nm = self.dynamicCall("GetMasterCodeName(QString)", code)

                    f = open("files/condition_stock.txt", "a", encoding="utf8")
                    msg = "%s;%s;%s\n" % (code, code_nm, self.calcul_data[0][1])

                    f.write(msg)
                    f.close()

                elif pass_success == False:
                    self.logger.debug("Granville target dropped.")

                self.calcul_data.clear()
                self.analytics_event_loop.exit()

    def get_code_list_by_market(self, market_code):
        '''
        종목 코드 반환
        :param market_code: 시장 코드
        :return:
        '''
        code_list = self.dynamicCall("GetCodeListByMarket(QString)", market_code)
        code_list = code_list.split(";")[:-1]

        return code_list

    def calculator_fnc(self):
        '''
        종목 분석 실행용 함수
        :return:
        '''
        code_list = self.get_code_list_by_market("10")
        self.logger.info("코스닥 종목 갯수 : %s" % len(code_list))

        ### 각 종목별 분석을 위해 Screen Number(4000)를 끊어서 요청
        for idx, code in enumerate(code_list):
            self.dynamicCall("DisconnectRealData(QString)", self.screen_calculate_Numner)
            self.logger.info("[ %s / %s ] : KOSDAQ Stock Code : %s is updating..." % (idx+1, len(code_list), code))

            self.day_kiwoom_db(code=code)

    def day_kiwoom_db(self, code=None, date=None, sPrevNext="0"):

        ### Eventloop가 멈추지 않고 다음 코드가 실행되기 전에 딜레이를 준다.
        QTest.qWait(3600)

        self.dynamicCall("SetInputValue(QString, QString)", "종목코드", code)
        self.dynamicCall("SetInputValue(QString, QString)", "수정주가구분", "1")

        if date != None:
            self.dynamicCall("SetInputValue(QString, QString)", "기준일자", date)

        self.dynamicCall("CommRqData(QString, QString, int, QString)", self.inquiry_daily_boxplot, "opt10081", sPrevNext, self.screen_calculate_Numner)

        self.analytics_event_loop.exec_()

    def read_code(self):

        if os.path.exists("files/condition_stock.txt"):
            f = open("files/condition_stock.txt", "r", encoding = "utf8")

            lines = f.readlines()
            for line in lines:
                if line != "":
                    ls = line.split(";")
                    stock_code = ls[0]
                    stock_name = ls[1]
                    stock_price = int(ls[2].split("\n")[0])
                    stock_price = abs(stock_price)

                    self.portfolio_stock_dict.update({stock_code: {"종목명":stock_name, "현재가":stock_price}})

            f.close()

    def screen_number_setting(self):

        # 주문에 필요한 스크린 생성하고 주문 준비
        screen_overwrite = []

        # 계좌평가 잔고내역에 있는 종목들 : 내가 이미 보유하고 있는 종목이 아니면 코드 추가
        for code in self.account_stock_dict.keys():
            if code not in screen_overwrite:
                screen_overwrite.append(code)

        # 미체결에 있는 종목들 : 미체결로 있는 종목들이 아니면 코드 추가
        for order_number in self.not_account_stock_dict.keys():
            code = self.not_account_stock_dict[order_number]['종목코드']

            if code not in screen_overwrite:
                screen_overwrite.append(code)

        # 포트폴리오에 담겨있는 종목들 : 분석해서 나온 종목 중에 포트폴리오에 없으면 추가
        for code in self.portfolio_stock_dict.keys():
            if code not in screen_overwrite:
                screen_overwrite.append(code)

        # 스크린번호 할당
        cnt = 0
        for code in screen_overwrite:

            # 두개를 따로 만드는 이유?
            temp_screen = int(self.screen_real_stock)
            meme_screen = int(self.screen_meme_stock)

            # 스크린 번호 안넘치게 보수적으로 50개씩 끊어서 생성
            if (cnt % 50) == 0:
                temp_screen += 1 # "5000" -> "5001" ; 50개당 스크린 번호 하나씩
                self.screen_real_stock = str(temp_screen)

            if (cnt % 50) == 0:
                meme_screen += 1
                self.screen_meme_stock = str(meme_screen)

            # 포트폴리오에 이미 있는 코드면 코드명으로 스크린 번호 업데이트
            if code in self.portfolio_stock_dict.keys():
                self.portfolio_stock_dict[code].update({"스크린번호" : str(self.screen_real_stock)})
                self.portfolio_stock_dict[code].update({"주문용스크린번호" : str(self.screen_meme_stock)})

            # 포트폴리오에 없는 코드면 코드 입력
            elif code not in self.portfolio_stock_dict.keys():
                self.portfolio_stock_dict.update({code: {"스크린번호" : str(self.screen_real_stock), "주문용스크린번호": str(self.screen_meme_stock)}})

            cnt += 1

        print(self.portfolio_stock_dict)

    def realdata_slot(self, sCode, sRealType, sRealData):
        '''

        :param sCode: 종목코드
        :param sRealType: 실시간타입
        :param sRealData: 실시간 데이터 전문(사용불가)
        :return:
        '''

        self.logger.info("실시간 데이터 조회 시작 [%s] "%sRealType)

        if sRealType == "장시작시간":
            fid = self.realType.REALTYPE[sRealType]['장운영구분']
            value = self.dynamicCall("GetCommRealData(QString, int)", sCode, fid)



            if value == '0':
                self.logger.info("장 시작 전")

            elif value == '3':
                self.logger.info("장 시작")

            elif value == '2':
                self.logger.info("장 종료, 동시호가로 넘어감")

            elif value == '4':
                self.logger.info("3시 30분 장 종료")

                for code in self.portfolio_stock_dict.keys():
                    self.dynamicCall("SetRealRemove(String, String)", self.portfolio_stock_dict[code]['스크린번호'], code)

                QTest.qWait(5000)

                self.file_delete()
                self.calculator_fnc()

                sys.exit()

        elif sRealType == "주식체결":
            accepted_time = self.dynamicCall("GetCommRealData(QString, int)", sCode, self.realType.REALTYPE[sRealType]['체결시간']) # HHMMSS
            current_price = self.dynamicCall("GetCommRealData(QString, int)", sCode, self.realType.REALTYPE[sRealType]['현재가'])
            compare_prev = self.dynamicCall("GetCommRealData(QString, int)", sCode, self.realType.REALTYPE[sRealType]['전일대비'])
            up_down_rate = self.dynamicCall("GetCommRealData(QString, int)", sCode, self.realType.REALTYPE[sRealType]['등락율'])
            priority_short_callvalue = self.dynamicCall("GetCommRealData(QString, int)", sCode, self.realType.REALTYPE[sRealType]['(최우선)매도호가'])
            priority_long_callvalue = self.dynamicCall("GetCommRealData(QString, int)", sCode, self.realType.REALTYPE[sRealType]['(최우선)매수호가'])
            volumn = self.dynamicCall("GetCommRealData(QString, int)", sCode, self.realType.REALTYPE[sRealType]['거래량(+는 매수체결, -는 매도체결)'])
            cumul_volumn = self.dynamicCall("GetCommRealData(QString, int)", sCode, self.realType.REALTYPE[sRealType]['누적거래량'])
            highest_price = self.dynamicCall("GetCommRealData(QString, int)", sCode, self.realType.REALTYPE[sRealType]['고가'])
            start_price = self.dynamicCall("GetCommRealData(QString, int)", sCode, self.realType.REALTYPE[sRealType]['시가'])
            lowest_price = self.dynamicCall("GetCommRealData(QString, int)", sCode, self.realType.REALTYPE[sRealType]['저가'])

            current_price = abs(int(current_price))
            compare_prev = abs(int(compare_prev))
            up_down_rate = float(up_down_rate)
            priority_short_callvalue = abs(int(priority_short_callvalue))
            priority_long_callvalue = abs(int(priority_long_callvalue))
            volumn = abs(int(volumn))
            cumul_volumn = abs(int(cumul_volumn))
            highest_price = abs(int(highest_price))
            start_price = abs(int(start_price))
            lowest_price = abs(int(lowest_price))

            if sCode not in self.portfolio_stock_dict:
                self.portfolio_stock_dict.update({sCode: {}})

            self.portfolio_stock_dict[sCode].update({"체결시간": accepted_time})
            self.portfolio_stock_dict[sCode].update({"현재가": current_price})
            self.portfolio_stock_dict[sCode].update({"전일대비": compare_prev})
            self.portfolio_stock_dict[sCode].update({"등락율": up_down_rate})
            self.portfolio_stock_dict[sCode].update({"(최우선)매도호가": priority_short_callvalue})
            self.portfolio_stock_dict[sCode].update({"(최우선)매수호가": priority_long_callvalue})
            self.portfolio_stock_dict[sCode].update({"거래량": volumn})
            self.portfolio_stock_dict[sCode].update({"누적거래량": cumul_volumn})
            self.portfolio_stock_dict[sCode].update({"고가": highest_price})
            self.portfolio_stock_dict[sCode].update({"시가": start_price})
            self.portfolio_stock_dict[sCode].update({"저가": lowest_price})

            # print(self.portfolio_stock_dict[sCode])

            # 실시간 거래
            # [매도] 계좌잔고평가내역에 있고 오늘 산 잔고에는 없을 경우
            if sCode in self.account_stock_dict.keys() and sCode not in self.jango_dict.keys():
                # print("%s %s"% ("신규 매도(1) ", sCode))

                order_code_inform = self.account_stock_dict[sCode]

                meme_rate = (current_price - order_code_inform['매입가']) / order_code_inform['매입가'] * 100

                if order_code_inform['매입가능수량'] > 0 and (meme_rate > 5 or meme_rate < -5):
                    order_success = self.dynamicCall("SendOrder(QString, QString, QString, QString, int, QString, int, int, QString, QString)",
                                     ["신규매도", # 쓰고 싶은 거래 이름
                                     self.portfolio_stock_dict[sCode]['주문용스크린번호'],
                                     self.account_num, #계좌번호
                                     2, # 주문유형 1:신규매수, 2:신규매도 3:매수취소, 4:매도취소, 5:매수정정, 6:매도정정
                                     sCode,
                                     order_code_inform['매매가능수량'],
                                     0, # 주문 가격 : 시장가인 경우 시장 가격 정보로 결정되므로 가격 정보 불필요
                                     self.realType.SENDTYPE['거래구분']['시장가'],
                                     '']) # 원주문 번호 : 정정/취소 주문을 하는 경우 본래 요청 번호
                    if order_success == 0:
                        print("매도 주문 전달 성공")
                        del self.account_stock_dict[sCode]
                    else:
                        print("매도 주문 전달 실패")


            # [매수] 오늘 산 잔고에 있을 경우
            elif sCode in self.jango_dict.keys():
                print("%s %s" % ("신규 매도(2) ", sCode))

                jango_dict_item = self.jango_dict[sCode]
                meme_rate = (current_price - jango_dict_item['매입단가']) / jango_dict_item['매입단가'] * 100

                if jango_dict_item['주문가능수량'] > 0 and (meme_rate > 5 or meme_rate < -5):
                    order_success = self.dynamicCall(
                                    "SendOrder(QString, QString, QString, QString, int, QString, int, int, QString, QString)",
                                    ["신규매도",  # 쓰고 싶은 거래 이름
                                     self.portfolio_stock_dict[sCode]['주문용스크린번호'],
                                     self.account_num,  # 계좌번호
                                     2,  # 주문유형 1:신규매수, 2:신규매도 3:매수취소, 4:매도취소, 5:매수정정, 6:매도정정
                                     sCode,
                                     jango_dict_item['주문가능수량'],
                                     0,  # 주문 가격 : 시장가인 경우 시장 가격 정보로 결정되므로 가격 정보 불필요
                                     self.realType.SENDTYPE['거래구분']['시장가'],
                                     ''])  # 원주문 번호 : 정정/취소 주문을 하는 경우 본래 요청 번호

                    if order_success == 0:
                        print("매도 주문 전달 성공")
                    else:
                        print("매도 주문 전달 실패")

            # [매수] 등락율이 2.0% 이상이고 오늘 산 잔고에 없는 경우
            elif up_down_rate > 2.0 and sCode not in self.jango_dict:

                result = (self.budget * 0.1) / current_price
                quantity = int(result)

                print("%s [%s] 주문용 스크린번호 [%s] 계좌번호 [%s] 수량 [%s] 가격 [%s] " % ("신규 매수 ", sCode, self.portfolio_stock_dict[sCode]['주문용스크린번호'], self.account_num, quantity, current_price))

                order_success = self.dynamicCall(
                    "SendOrder(QString, QString, QString, QString, int, QString, int, int, QString, QString)",
                    ["신규매수",  # 쓰고 싶은 거래 이름
                     self.portfolio_stock_dict[sCode]['주문용스크린번호'],
                     self.account_num,  # 계좌번호
                     1,  # 주문유형 1:신규매수, 2:신규매도 3:매수취소, 4:매도취소, 5:매수정정, 6:매도정정
                     sCode,
                     quantity,
                     current_price,  # 주문 가격 : 시장가인 경우 시장 가격 정보로 결정되므로 가격 정보 불필요
                     self.realType.SENDTYPE['거래구분']['지정가'],
                     ""])  # 원주문 번호 : 정정/취소 주문을 하는 경우 본래 요청 번호

                if order_success == 0:
                    print("매수 주문 전달 성공")
                else:
                    print("매수 주문 전달 실패 [%s]" % order_success)

            not_meme_list = list(self.not_account_stock_dict)

            for order_num in not_meme_list:
                code = self.not_account_stock_dict[order_num]["종목코드"]
                meme_price = self.not_account_stock_dict[order_num]["주문가격"]
                not_quantity = self.not_account_stock_dict[order_num]["미체결수량"]
                order_gubun = self.not_account_stock_dict[order_num]["주문구분"]

                # 매수 취소
                if order_gubun == "매수" and not_quantity > 0 and priority_short_callvalue > meme_price:
                    print("%s %s" % ("매수 취소(1) ", sCode))

                    if order_gubun == "신규매수" and not_quantity > 0 and current_price > meme_price:
                        order_success = self.dynamicCall(
                            "SendOrder(QString, QString, QString, QString, int, QString, int, int, QString, QString)",
                            ["매수취소",  # 쓰고 싶은 거래 이름
                             self.portfolio_stock_dict[sCode]['주문용스크린번호'],
                             self.account_num,  # 계좌번호
                             3,  # 주문유형 1:신규매수, 2:신규매도 3:매수취소, 4:매도취소, 5:매수정정, 6:매도정정
                             sCode,
                             0,
                             0,  # 주문 가격 : 시장가 & 매수 취소인 경우 시장 가격 정보로 결정되므로 가격 정보 불필요
                             self.realType.SENDTYPE['거래구분']['지정가'],
                             order_num])  # 원주문 번호 : 정정/취소 주문을 하는 경우 본래 요청 번호

                    if order_success == 0:
                        print("매수취소 주문 전달 성공")
                    else:
                        print("매수취소 주문 전달 실패")

                elif not_quantity == 0:
                    del self.not_account_stock_dict[order_num]


    def chejan_slot(self, sGubun, nItemCnt, sFIdList):
        '''

        :param sGubun: 체결구분.접수와 체결시 0값, 국내주식 잔고변경은 '1'값, 파생잔고변경은 '4'
        :param nItemCnt:
        :param sFIdList:
        :return:
        '''


        # 체결/접수 변경
        if int(sGubun) == 0:
            account_num = self.dynamicCall("GetChejanData(int)", self.realType.REALTYPE['주문체결']['계좌번호'])
            sCode = self.dynamicCall("GetChejanData(int)", self.realType.REALTYPE['주문체결']['종목코드,업종코드'])[1:]
            stock_name = self.dynamicCall("GetChejanData(int)", self.realType.REALTYPE['주문체결']['종목명'])
            order_origin_number = self.dynamicCall("GetChejanData(int)", self.realType.REALTYPE['주문체결']['원주문번호'])
            order_number = self.dynamicCall("GetChejanData(int)", self.realType.REALTYPE['주문체결']['주문번호'])
            order_status = self.dynamicCall("GetChejanData(int)", self.realType.REALTYPE['주문체결']['주문상태'])
            order_quantity = self.dynamicCall("GetChejanData(int)", self.realType.REALTYPE['주문체결']['주문수량'])
            order_price = self.dynamicCall("GetChejanData(int)", self.realType.REALTYPE['주문체결']['주문가격'])
            not_chegual_quan = self.dynamicCall("GetChejanData(int)", self.realType.REALTYPE['주문체결']['미체결수량'])
            order_gubun = self.dynamicCall("GetChejanData(int)", self.realType.REALTYPE['주문체결']['주문구분'])
            chegual_time_str = self.dynamicCall("GetChejanData(int)", self.realType.REALTYPE['주문체결']['주문/체결시간'])
            chegual_price = self.dynamicCall("GetChejanData(int)", self.realType.REALTYPE['주문체결']['체결가'])
            chegual_quantity = self.dynamicCall("GetChejanData(int)", self.realType.REALTYPE['주문체결']['체결량'])
            current_price = self.dynamicCall("GetChejanData(int)", self.realType.REALTYPE['주문체결']['현재가'])
            first_sell_price = self.dynamicCall("GetChejanData(int)", self.realType.REALTYPE['주문체결']['(최우선)매도호가'])
            first_buy_price = self.dynamicCall("GetChejanData(int)", self.realType.REALTYPE['주문체결']['(최우선)매수호가'])


            stock_name = stock_name.strip()
            order_quantity = int(order_quantity)
            order_price = int(order_price)
            not_chegual_quan = int(not_chegual_quan)
            order_gubun = order_gubun.strip().lstrip('+').lstrip('-')
            chegual_price = 0 if chegual_price == '' else int(chegual_price)
            chegual_quantity = 0 if chegual_quantity == '' else int(chegual_quantity)
            current_price = abs(int(current_price))
            first_sell_price = abs(int(first_sell_price))
            first_buy_price = abs(int(first_buy_price))

            # 미체결 수량에 주문 번호가 없는 경우
            if order_number not in self.not_account_stock_dict.keys():
                self.not_account_stock_dict.update({order_number : {}})

            self.not_account_stock_dict[order_number].update({"종목코드,업종코드": sCode})
            self.not_account_stock_dict[order_number].update({"종목명": stock_name})
            self.not_account_stock_dict[order_number].update({"원주문번호": order_origin_number})
            self.not_account_stock_dict[order_number].update({"주문번호": order_number})
            self.not_account_stock_dict[order_number].update({"주문상태": order_status})
            self.not_account_stock_dict[order_number].update({"주문수량": order_quantity})
            self.not_account_stock_dict[order_number].update({"주문가격": order_price})
            self.not_account_stock_dict[order_number].update({"미체결수량": not_chegual_quan})
            self.not_account_stock_dict[order_number].update({"주문구분": order_gubun})
            self.not_account_stock_dict[order_number].update({"주문/체결시간": chegual_time_str})
            self.not_account_stock_dict[order_number].update({"체결가": chegual_price})
            self.not_account_stock_dict[order_number].update({"체결량": chegual_quantity})
            self.not_account_stock_dict[order_number].update({"현재가": current_price})
            self.not_account_stock_dict[order_number].update({"(최우선)매도호가)": first_sell_price})
            self.not_account_stock_dict[order_number].update({"(최우선)매수호가": first_buy_price})

            print(self.not_account_stock_dict)

        # 잔고 변경
        elif int(sGubun) == 1:
            print("잔고")

            account_num = self.dynamicCall("GetChejanData(int)", self.realType.REALTYPE['잔고']['계좌번호'])
            sCode = self.dynamicCall("GetChejanData(int)", self.realType.REALTYPE['잔고']['종목코드,업종코드'])[1:]
            stock_name = self.dynamicCall("GetChejanData(int)", self.realType.REALTYPE['잔고']['종목명'])
            current_price = self.dynamicCall("GetChejanData(int)", self.realType.REALTYPE['잔고']['현재가'])
            stock_quan = self.dynamicCall("GetChejanData(int)", self.realType.REALTYPE['잔고']['보유수량'])
            like_quan = self.dynamicCall("GetChejanData(int)", self.realType.REALTYPE['잔고']['주문가능수량'])
            buy_price = self.dynamicCall("GetChejanData(int)", self.realType.REALTYPE['잔고']['매입단가'])
            total_buy_price = self.dynamicCall("GetChejanData(int)", self.realType.REALTYPE['잔고']['총매입가(당일누적)'])
            meme_gubun = self.dynamicCall("GetChejanData(int)", self.realType.REALTYPE['잔고']['매도/매수구분'])
            first_sell_price = self.dynamicCall("GetChejanData(int)", self.realType.REALTYPE['잔고']['(최우선)매도호가'])
            first_buy_price = self.dynamicCall("GetChejanData(int)", self.realType.REALTYPE['잔고']['(최우선)매수호가'])

            stock_name = stock_name.strip()
            current_price = abs(int(current_price))
            stock_quan = int(stock_quan)
            like_quan = int(like_quan)
            buy_price = abs(int(buy_price))
            total_buy_price = int(total_buy_price)
            meme_gubun = self.realType.REALTYPE['매도수구분'][meme_gubun]
            first_sell_price = abs(int(first_sell_price))
            first_buy_price = abs(int(first_buy_price))

            if sCode not in self.jango_dict.keys():
                self.jango_dict.update({sCode:{}})

            self.jango_dict[sCode].update({"현재가":current_price})
            self.jango_dict[sCode].update({"종목코드,업종코드": sCode})
            self.jango_dict[sCode].update({"종목명": stock_name})
            self.jango_dict[sCode].update({"보유수량": stock_quan})
            self.jango_dict[sCode].update({"주문가능수량": like_quan})
            self.jango_dict[sCode].update({"매입단가": buy_price})
            self.jango_dict[sCode].update({"총매입가(당일누적)": total_buy_price})
            self.jango_dict[sCode].update({"매도/매수구분": meme_gubun})
            self.jango_dict[sCode].update({"(최우선)매도호가": first_sell_price})
            self.jango_dict[sCode].update({"(최우선)매수호가": first_buy_price})

            if stock_quan == 0:
                del self.jango_dict[sCode]
                self.dynamicCall("SetRealRemove(QString, QString)", self.portfolio_stock_dict[sCode]['스크린번호'], sCode)


    def msg_slot(self, sScrNo, sRQName, sTrCode, msg):
        '''
        증권사 메시지 송수신
        :param sScrNo:
        :param sRQName:
        :param sTrCode:
        :param msg:
        :return:
        '''
        self.logger.debug("[msg_slot] 스크린번호 : %s, 요청이름 : %s, 코드 : %s --- %s" % (sScrNo, sRQName, sTrCode, msg))

    # 파일 삭제
    def file_delete(self):
        if os.path.isfile("files/condition_stock.txt"):
            os.remove("files/condition_stock.txt")


