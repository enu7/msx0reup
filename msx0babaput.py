# msx0babaput.py
import sys
import telnetlib
import time
import re
import base64
import os
import difflib
import threading

def is_valid_filename(filename):
    # ファイル名が8文字+拡張子3文字であるかどうかをチェックする正規表現
    pattern = r'^[A-Za-z0-9_-]{1,8}\.[A-Za-z0-9_-]{3}$'
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
        if line.startswith("LIST"):
            capture = True
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
    # 両方のテキストを行に分割し、空白行と行番号20を除外
    lines1 = [line.strip() for line in text1.splitlines() if line.strip() and not line.strip().startswith("20 ")]
    lines2 = [line.strip() for line in text2.splitlines() if line.strip() and not line.strip().startswith("20 ")]
   
    # difflib.SequenceMatcherを使用して類似度を計算
    matcher = difflib.SequenceMatcher(None, lines1, lines2)
    similarity = matcher.ratio()
    
    # 差分を表示
    diff = list(difflib.ndiff(lines1, lines2))
    print("Differences:")
    for line in diff:
        print(line)
    
    # 完全に一致する場合のみTrueを返す
    return similarity == 1.0


def msx0babaput(host, program, message_file_path, cancel_flag, timeout=8):
    start_time = time.time()
    message_file_name = os.path.basename(message_file_path)
    if not is_valid_filename(message_file_name):
        return "Invalid file name format. ",0
    max_retries = 1
    retry_delay = 3  # 3秒後にリトライ

    for attempt in range(max_retries + 1):
        try:
            # Telnet接続
            print(f"msx0babaput started connecting to msx0 (Attempt {attempt + 1})")
            sys.stdout.write("Start initilizing.")
            sys.stdout.flush()
            tn = telnetlib.Telnet(host, 2223, timeout=timeout)

            # タイムアウト付きの読み取り関数
            def read_until_timeout(expected, timeout):
                def _read_thread(tn, result):
                    try:
                        result.append(tn.read_until(expected, timeout))
                    except EOFError:
                        result.append(None)
                result = []
                thread = threading.Thread(target=_read_thread, args=(tn, result))
                thread.start()
                thread.join(timeout)
                if thread.is_alive():
                    tn.close()  # 接続を強制的に閉じる
                    raise TimeoutError("Operation timed out")
                if not result:
                    raise TimeoutError("Operation timed out")
                return result[0]

            # DOSモードで起動している場合、BASICインタープリタモードに切り替える
            tn.write(b'\r\n')
            response = tn.read_until(b'A>', timeout=1)  # 1秒以内にプロンプトが表>示されない場合はタイムアウト


            if b'A>' in response:
                tn.write(b'basic\r\n')  # BASICインタープリタモードに切り替え
                read_until_timeout(b'Ok', timeout)

                sys.stdout.write("Start building base64decoder on msx0 basic.")
                sys.stdout.flush()
                program = program + '\r\n20 LET F$ = "' + message_file_name + '"\r\n'
                
                retry=1
                for i in range(0,retry):
                    # BASICプログラムをサーバに送信
                    tn.write(program.encode('ascii') + b"\r\n") 
                    tn.write(b'LIST\r\n')
                    response = tn.read_until(b'Ok').decode("utf-8")
                    print(response)
                    extracted = extract_list_to_ok(response)
                    print(extracted)
                    if is_match(extracted,program):#プログラム転送ミスがなければ処理を進める
                        break
                    print("retry")

            else:
                # プログラムが既に存在するかチェック
                tn.write(b'LIST 10\r\n')
                existing_program = tn.read_until(b'Ok').decode("utf-8")
                if "10 DEFINT" in existing_program and attempt==0:  # プログラムが既に存在する場合
                    print("Existing program detected. Updating file name only.")
                    tn.write(f'20 LET F$ = "{message_file_name}"\r\n'.encode('ascii'))
#                    tn.read_until(b'Ok')
                    sys.stdout.write("\rStart initilizing..Skip.")
                    sys.stdout.flush()
                    print()
                else:
                    tn.write(b'new\r\n')	
                    #tn.read_until(b'Ok')
                    read_until_timeout(b'Ok', timeout)
                    sys.stdout.write("\rStart initilizing..Done.")
                    sys.stdout.flush()
                    print()

                    sys.stdout.write("Start building base64decoder on msx0 basic.")
                    sys.stdout.flush()
                    program = program + '\r\n20 LET F$ = "' + message_file_name + '"\r\n'
                    
                    retry=1
                    for i in range(0,retry):
                        # BASICプログラムをサーバに送信
                        tn.write(program.encode('ascii') + b"\r\n") 
                        tn.write(b'LIST\r\n')
                        response = tn.read_until(b'Ok').decode("utf-8")
                        print(response)
                        extracted = extract_list_to_ok(response)
                        print(extracted)
                        if is_match(extracted,program):#プログラム転送ミスがなければ処理を進める
                            break
                        print("retry")

            #プログラム実行
            tn.write(b'run\r\n') 
            read_until_timeout(b'?', timeout)#tn.read_until(b'?')
            sys.stdout.write("\rStart building base64decoder on msx0 basic..Done.")
            print()

            print("Start Transferring a target file to msx0 basic")
            # メッセージをBase64エンコードして送信
            with open(message_file_path, 'rb') as file:
                messages = file.read()
            
            base64_message = base64.b64encode(messages).decode('ascii')
            total_chunks = len(base64_message) // 76
            for i in range(0, len(base64_message), 76):
                if cancel_flag.is_set():
                    # "`"を送信し、BASICプログラムを終了
                    tn.write(b'`\r\n') 
                    read_until_timeout(b'Ok', timeout)#tn.read_until(b'Ok')
                    return "Upload cancelled", time.time() - start_time
                tn.write(base64_message[i:i+76].encode('ascii') + b"\r\n")  # 改行コードをCR+LFに変更
                read_until_timeout(b'?', timeout)#tn.read_until(b'?')
                # インジケータ表示
                sys.stdout.write("\rTransferring: {}/{} chunks".format(i//76, total_chunks))
                sys.stdout.flush()
            print()
            end_time = time.time()
            execution_time = end_time - start_time

            # "`"を送信し、BASICプログラムを終了
            tn.write(b'`\r\n') 
            read_until_timeout(b'Ok', timeout)#tn.read_until(b'Ok')
            result="Done"

            return result,  execution_time
        
        except Exception as e:
            if attempt < max_retries:
                print(f"Connection failed. Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
            else:
                return f"Failed after {max_retries + 1} attempts: {str(e)}", 0

        finally:
            # Telnet接続を閉じる
            try:
                if tn:
                    tn.close()
                    time.sleep(retry_delay)
            except:
                pass  # 接続が既に閉じている場合のエラーを無視

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python msx0babaput.py <host> <message_file_path>")
        sys.exit(1)

    host = sys.argv[1]
    message_file_path = sys.argv[2]

    # BASICプログラム
    basic_program = '''
10 DEFINT A-Z:DIM F$, I$, O$, B$, T$, C$, B(4), OB(3):CLEAR 10000\r\n
20 LET F$ = "OUTPUT.BIN"\r\n
30 ON ERROR GOTO 9000:KILL F$\r\n
40 S=57:OPEN F$ AS #1 LEN=S\r\n
50 INPUT ":"; I$\r\n
60 IF I$="`" THEN CLOSE #1:END\r\n
70 GOSUB 100\r\n
80 GOSUB 1000\r\n
90 GOTO 50\r\n
100 'Decode\r\n
110 LET O$ = ""\r\n
120 LET B$ = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/"\r\n
130 FOR I = 1 TO LEN(I$) STEP 4\r\n
140   T$ = MID$(I$, I, 4)\r\n
170   FOR J = 1 TO 4\r\n
180     B(J) = 0\r\n
190   NEXT J\r\n
200   FOR J = 1 TO 4\r\n
210     B(J) = INSTR(B$, MID$(T$, J, 1)) - 1:IF B(J) < 0 THEN B(J)=0\r\n
220   NEXT J\r\n
230   OB(1) = B(1) * 4 + B(2) \ 16\r\n
240   OB(2) = (B(2) AND 15) * 16 + B(3) \ 4\r\n
250   OB(3) = (B(3) AND 3) * 64 + B(4)\r\n
260   FOR J = 1 TO 3\r\n
270     O$ = O$ + CHR$(OB(J))\r\n
280   NEXT J\r\n
290 NEXT I\r\n
300 LET O$ = LEFT$(O$, LEN(O$) + (MID$(T$, 3, 1) = "=") + (MID$(T$, 4, 1) = "="))\r\n
310 RETURN\r\n
1000 'SAVE\r\n
1010 IF LEN(O$)<S THEN 1100\r\n
1020 FIELD #1,INT(S) AS T$\r\n
1030 LSET T$=O$:PUT #1\r\n
1040 RETURN\r\n
1100 CLOSE#1\r\n
1110 S=1:OPEN F$ AS #1 LEN=S\r\n
1120 F=LOF(1)\r\n
1130 FIELD #1,1 AS T$\r\n
1140 FOR I=1 TO LEN(O$)\r\n
1150   LSET T$=MID$(O$,I,1)\r\n
1160   PUT #1,F+I\r\n
1170 NEXT I\r\n
1180 RETURN\r\n
9000 IF ERL=30 AND ERR=53 THEN RESUME 40\r\n
9100 ON ERROR GOTO 0\r\n
'''

    # 全プロセスを実行
    result, execution_time = msx0babaput(host, basic_program, message_file_path,timeout=10)
    print(result)
    print("Execution time: {} seconds".format(execution_time))