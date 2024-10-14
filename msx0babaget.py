import sys
import telnetlib
import time
import re
import base64
import os
from datetime import datetime
import difflib

def is_valid_filename(filename):
    # ファイル名が8文字+拡張子3文字であるかどうかをチェックする正規表現
    pattern = r'^[A-Za-z0-9_-]{1,8}(\.[A-Za-z0-9_-]{1,3})?$'
    return re.match(pattern, filename)

def extract_list_to_ok(text):
    # 文字列を行に分割
    lines = text.splitlines()
    
    # 抽出する文字列を保持する変数
    extracted = ""
    capture = False
    
    # 各行をイテレート
    for line in lines:
        # "LIST"で始まる行を見つけたら、抽出を開始
        if line.startswith("2 'msx0babaput_encoder"):
            capture = True
            extracted += line + "\r\n\n"
        # "Ok"で始まる行を見つけたら、抽出を終了
        elif line.startswith("Ok"):
            break
        # 抽出中であれば、行を追加
        elif capture:
            extracted += line + "\r\n\n"
    
    return extracted

#差分チェック。行に化けがなければよしとする
def is_match(text1, text2):
    print("text1:")
    print(text1)
    print("text2:")
    print(text2)
    
    # 両方のテキストを行に分割
    lines1 = text1.splitlines()
    lines2 = text2.splitlines()
    # 両方のテキストを行に分割し、空白行と行番号1と行番号20を除外
    lines1 = [line.strip() for line in text1.splitlines() if line.strip() and not line.strip().startswith("1 ") and not line.strip().startswith("20 ")]
    lines2 = [line.strip() for line in text2.splitlines() if line.strip() and not line.strip().startswith("1 ") and not line.strip().startswith("20 ")]
   
    # difflib.SequenceMatcherを使用して類似度を計算
    matcher = difflib.SequenceMatcher(None, lines1, lines2)
    similarity = matcher.ratio()
    print("lines1:")
    print(lines1)
    print("lines2:")
    print(lines2)
    # 差分を表示
    diff = list(difflib.ndiff(lines1, lines2))
    print("Differences:")
    for line in diff:
        print(line)
    
    # 完全に一致する場合のみTrueを返す
    return similarity == 1.0

def create_new_file(file_name):
    open(file_name, 'wb').close()

def decode_and_write_to_file(encoded_text, file_name):
    decoded_data = base64.b64decode(encoded_text)
    with open(file_name, 'ab') as file:
        file.write(decoded_data)

def get_file_from_MSX0(host, program, program_ver, message_file_path,local_file_path):
    start_time = time.time()
    message_file_name = os.path.basename(message_file_path)
    if not is_valid_filename(message_file_name):
        return "Invalid file name format.", time.time() - start_time
    try:
        # Telnet接続
        print("msx0babaput started connecting to msx0")
        tn = telnetlib.Telnet(host, 2223)
        tn.write(b'\r\n')

        # DOSモードで起動している場合、BASICインタープリタモードに切り替える
        response = tn.read_until(b'A>', timeout=1)  # 1秒以内にプロンプトが表>示されない場合はタイムアウト
        if b'A>' in response:
            tn.write(b'basic\r\n')  # BASICインタープリタモードに切り替え
            tn.read_until(b'Ok')

        # ファイルサイズを取得
        oneline='OPEN"' + message_file_name + '"AS#1:PRINT LOF(1):CLOSE#1\r\n'
        tn.write(oneline.encode('ascii'))
        output = tn.read_until(b"Ok\r\n").decode('ascii').strip()
        match = re.search(r'\s+(\d+)\s+', output)
        message_file_size = 0
        if match:
            message_file_size = int(match.group(1))
        else:
            print("Can not get file size!")
            return "Error", time.time() - start_time
        print("Target file name:"+ message_file_name +" size:" + str(message_file_size))

        #　MSX0上のプログラムバージョン確認
        tn.write(b'list 1-2\r\n') #行番号1-2を表示
        # response = tn.read_until(b'Ok', timeout=1)  # 1秒以内にプロンプトが表>示されない場合はタイムアウト
        existing_program = tn.read_until(b'Ok', timeout=1).decode("utf-8")
        if "2 'msx0babaput_encoder" in existing_program:
            sys.stdout.write("already initializing.")
            sys.stdout.flush()
            print()
            # BASICプログラムをBASICインタープリタに送信する(ファイル名のみ)
            sys.stdout.write("Start building base64encoder on msx0 basic.")
            sys.stdout.flush()
            program_to_send  = '5020 LET F$ = "' + message_file_name + '"\r\n'#ファイル名を上書き
            tn.write(program_to_send.encode('ascii') + b"\r\n") # BASICプログラムをサーバに送信
            result = tn.read_until(b'\r\n\r\n')
            sys.stdout.write("\rStart building base64encoder on msx0 basic..Done")
            sys.stdout.flush()
            print()
        else:
            if  "1 'msx0babaput_decoder" in existing_program:  # Encoderプログラムが既に存在する場合
                sys.stdout.write("\rStart initilizing..Skip.")
                sys.stdout.flush()
                print()
            else:
                # newコマンドで初期化
                sys.stdout.write("Start initializing.")
                sys.stdout.flush()
                tn.write(b'new\r\n')
                tn.read_until(b'Ok\r\n')
                sys.stdout.write("\rStart initializing..Done.")
                sys.stdout.flush()
                print()
            # BASICプログラムをBASICインタープリタに送信する
            sys.stdout.write("Start building base64encoder on msx0 basic.")
            sys.stdout.flush()
            program_to_send  = program + '5020 LET F$ = "' + message_file_name + '"\r\n'#ファイル名を上書き

            retry=1
            for i in range(0,retry):
                # BASICプログラムをサーバに送信
                tn.write(program_to_send.encode('ascii') + b"\r\n") 
                tn.write(b'LIST 5000-6000\r\n')
                response = tn.read_until(b'Ok').decode("utf-8")
                print("Response:"+response)
                extracted = extract_list_to_ok(response)
                if is_match(extracted,program_to_send):#プログラム転送ミスがなければ処理を進める
                    break
                print("retry")



            sys.stdout.write("\rStart building base64encoder on msx0 basic..Done")
            sys.stdout.flush()
            print()

        # BASICプログラムを実行する
        print("Start transfer a target file on msx0 basic to local PC.")
        create_new_file(local_file_path)
        tn.write(b'run 5000\r\n') 
        tn.read_until(b'run 5000\r\n')
        chunk_counter=0
        total_chunks= message_file_size // 57 +1
        # BASICプログラムの結果を1行ずつ読み取り、base64デコードしファイルに書き込む
        while True:
            sys.stdout.write("\rTransferring: {}/{} chunks".format(chunk_counter, total_chunks))
            sys.stdout.flush()
            result = tn.read_until(b'\n')  
            if "Ok\r\n" == result.decode('ascii'):
                break
            decode_and_write_to_file(result.decode('ascii').strip(),local_file_path)
            chunk_counter += 1
        result="Done"
        print()
        print(result)
        print("Execution time: {} seconds".format(time.time() - start_time))

        return result,  time.time() - start_time



    finally:
        # Telnet接続を閉じる
        tn.close()


if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Usage: python msx0babaget.py <host> <message_file_path> <local_file_path>")
        sys.exit(1)

    host = sys.argv[1]
    message_file_path = sys.argv[2]
    local_file_path = sys.argv[3]

    # BASICプログラム
    encoder_program = '''
2 'msx0babaput_encoder\r\n
5005 CALL IOTPUT("msx/u0/pm/cpu/percent",200)\r\n
5010 DEFINT A-Z:DIM B$,I$,X%,Y%,Z%,O%,P%,Q%,R%,OB%(4) :CLEAR 1000\r\n
5020 F$ = "messages.txt"\r\n
5030 B$ = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/"\r\n
5100 S = 3:OPEN F$ AS #1 LEN=S\r\n
5110 L = LOF(1): IF L=0 THEN 450 ELSE C = (L-1) \ S\r\n
5120 FIELD #1, 3 AS I$\r\n
5130 FOR H=1 TO C\r\n
5150   GET #1\r\n
5160   X% = ASC(MID$(I$, 1, 1))\r\n
5170   Y% = ASC(MID$(I$, 2, 1))\r\n
5180   Z% = ASC(MID$(I$, 3, 1))\r\n
5190   PRINT  MID$(B$, X% \ 4 + 1, 1) + MID$(B$, (X% AND 3) * 16 + Y% \ 16 + 1, 1);\r\n
5200   PRINT  MID$(B$, (Y% AND 15) * 4 + Z% \ 64 + 1, 1) + MID$(B$, (Z% AND 63) + 1, 1);\r\n
5210   IF H MOD 19 = 0 THEN PRINT  \r\n
5220 NEXT\r\n
5300 S = (L - 1) MOD 3\r\n
5320 GET #1\r\n
5340 X% = ASC(MID$(I$, 1, 1))\r\n
5350 Y% = ASC(MID$(I$, 2, 1))*(1+S=1)\r\n
5360 Z% = ASC(MID$(I$, 3, 1))*(1+(S=1 OR S=2))\r\n
5370 OB%(1) = X% \ 4\r\n
5380 OB%(2) = (X% AND 3) * 16 + Y% \ 16\r\n
5390 OB%(3) = (Y% AND 15) * 4 + Z% \ 64\r\n
5400 OB%(4) = Z% AND 63\r\n
5420 FOR J = 1 TO 4\r\n
5430   IF J >= 3 AND S= 1 THEN PRINT"="; 
       ELSE IF J = 4 AND S= 2 THEN PRINT"="; ELSE PRINT MID$(B$, OB%(J) + 1, 1);\r\n
5440 NEXT\r\n
5450 PRINT \r\n
5460 CLOSE #1\r\n
5500 CALL IOTPUT("msx/u0/pm/cpu/percent",100)\r\n
5999 END\r\n'''
 
    # 全プロセスを実行
    program_ver= datetime.now().strftime("%Y%m%d_%H%M%S")
    get_file_from_MSX0(host, encoder_program, program_ver, message_file_path,local_file_path)
