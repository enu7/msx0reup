![image](https://github.com/user-attachments/assets/9514b0f6-918e-47f3-8c80-58329f70fd72)
# MSX0 REMOTE UPLOADER version 0.1.2
MSX0 REMOTE UPLOADERは、MSX0に対してリモートからファイルをアップロードすることを膜的としたPythonプログラムです。
# 使用について
まだベータ版で品質はまだまだです。その点をご理解いただいたうえでご使用ください。
# 既知の問題
1. MSX0へのアップロードが遅い
2. 複数のファイル転送が全て成功したのかどうか表示していない
3. 一時ファイル領域がフォルダに対応していない

などなど
# 動作環境
開発と動作確認に使用している環境は以下の通りです。
- Windows 11
- Python 3.10.11
- kivy2.2.1

Pythonとkivyが動作する環境であれば動作させたいと考えていますが、環境がないため動作未確認です。
# インストール
pipコマンドで以下のPythonモジュールをインストールしてください。
```
pip install kivy
pip install pyjnius
pip install html2text
pip install lhafile
pip install chardet
pip install python-magic
pip install beautifulsoup4
```
Githubのメニュー<CODE>からDownload ZiPで一式ダウンロードし解凍してください。

# 起動方法
解凍後のフォルダで以下を実行するとGUIが起動します。
```python ./main.py```

# 簡易的な使い方
## テキストブラウザエリア
![image](https://github.com/enu7/msx0reup/blob/main/icon/go_back_btn.png) テキストブラウザの戻るボタン
![image](https://github.com/enu7/msx0reup/blob/main/icon/load_url_btn.png) テキストブラウザのURLに進むボタン
![image](https://github.com/enu7/msx0reup/blob/main/icon/download_file_btn.png) URL先のファイルを一時領域に保存するボタン
![image](https://github.com/enu7/msx0reup/blob/main/icon/local_copy_btn.png) ローカルファイルを一時領域に保存するボタン
[Date↑] 一時領域のファイルをソートするボタン
## 一時領域エリア
![image](https://github.com/enu7/msx0reup/blob/main/icon/toggle_all_checkboxes_btn.png) 一時領域のファイルをすべて選択するボタン
![image](https://github.com/enu7/msx0reup/blob/main/icon/refresh_file_list_btn.png) 一時領域のファイル表示を更新するボタン
![image](https://github.com/enu7/msx0reup/blob/main/icon/delete_selected_files_btn.png) 選択したファイルをすべて削除するボタン
![image](https://github.com/enu7/msx0reup/blob/main/icon/delete_btn.png) 該当ファイルを削除するボタン
![image](https://github.com/enu7/msx0reup/blob/main/icon/extract_btn.png) 該当DSKファイルからファイルを取り出すボタン
![image](https://github.com/enu7/msx0reup/blob/main/icon/unzip_btn.png) 該当ZIP/LZHファイルを解凍するボタン
[CONF CR+LF] 該当ファイルの改行コードをCR+LFに置換するボタン
## 転送機能エリア
![image](https://github.com/enu7/msx0reup/blob/main/icon/upload_file_btn.png) 選択した一時領域のファイルをMSX0にアップロードするボタン
注意：転送速度は遅いです
## MSX0一覧エリア
![image](https://github.com/enu7/msx0reup/blob/main/icon/add_msx0_list_btn.png) MSX0を表示リストに追加するボタン
![image](https://github.com/enu7/msx0reup/blob/main/icon/refresh_file_list_btn.png) MSX0リスト表示を更新するボタン
![image](https://github.com/enu7/msx0reup/blob/main/icon/cmd_btn.png) 該当MSX0上でコマンドを実行するボタン
![image](https://github.com/enu7/msx0reup/blob/main/icon/disk_change_btn.png) 該当MSX0上でDSKを入れ替えるボタン
![image](https://github.com/enu7/msx0reup/blob/main/icon/reset_btn.png) 該当MSX0をリセットするボタン
注意：リモートコントロールパネルと同じポート2224を使用するため、リモートコントロールパネルと同時に利用できません。
![image](https://github.com/enu7/msx0reup/blob/main/icon/remove_btn.png) 該当MSX0を表示リストから外すボタン
![image](https://github.com/enu7/msx0reup/blob/main/icon/exec_btn.png) ![image](https://github.com/enu7/msx0reup/blob/main/icon/run_btn.png) 該当ファイルを実行するボタン
![image](https://github.com/enu7/msx0reup/blob/main/icon/delete_btn.png) 該当ファイルを削除するボタン
## その他
[Settings] MSX0 Remote Uploaderの設定を変更するボタン
▽設定項目
  Temporary Folder: MSX0 Remote Uploderを実行したパソコンで一時的にファイルを保管する場所を指定します
  Default Download URL: テキストブラウザで最初に表示するサイトのURLを指定します
  Dfault MSX0 IP: MSX0のIP入力欄のデフォルト値を指定します
  BASIC Program PATH: MSX0側でbase64テキストを受信しデコードを行うBASICプログラムを指定します。チューニングしてください。
 
# 転送の作り
![image](https://github.com/enu7/msx0reup/blob/main/images/msx0reup_design.png)
MSX0 Remote UploaderはMSX0の2223ポートにtelnet接続し、リモートからMSX0にファイルを転送します。
作りは単純です。MSX0 Remote Uploaderはtelnet接続後、BASICの受信プログラムをMSX0に送信し実行、受信待ち受け状態のMSX0に対し、base64エンコードしたテキスト文を送信し、受信側は受信したファイルを逐次保存します。ファイル全体を送信し終わったら、終端コードを送付し、受け取った受信プログラムは終了します。

# 課題
現在のバージョンのMSX0 Remote Uploaderには以下の3点の課題があります。
1. アップロード速度が遅いです。マシン語実装にすると早くなることは確認済みです。
2. 一時領域はフォルダに対応していません。後回しにしています。
3. テキストブラウザが貧弱です。

今後徐々に改善してゆく予定です。

# アップロード高速化
https://qiita.com/enu7/items/23cab122141fb8d07c6d#%E6%9C%80%E5%BE%8C%E3%81%AB

上記リンクの「最後に」の章から、「basic_program = '''」以降のBASICプログラムを抜き出して、改行コード「\r\n」を削除して、適当な名前で保存し、msx0reupのSettingボタンからbasicファイルを差し替えれば、藤田さん作のマシン語記述のエンコーダが使えて高速化が図れます。

それでも、まだまだ遅いので高速化を検討しなければなりませんね。

# 変更履歴
今後追記
