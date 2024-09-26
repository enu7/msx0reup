![image](https://github.com/user-attachments/assets/9514b0f6-918e-47f3-8c80-58329f70fd72)
# MSX0 REMOTE UPLOADER
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
```
python ./main.py
```

# 簡易的なな使い方

# 転送の作り
![image](https://github.com/enu7/msx0reup/blob/main/images/msx0reup_design.png)

# アップロード高速化
https://qiita.com/enu7/items/23cab122141fb8d07c6d#%E6%9C%80%E5%BE%8C%E3%81%AB

上記リンクの「最後に」の章から、「basic_program = '''」以降のBASICプログラムを抜き出して、改行コード「\r\n」を削除して、適当な名前で保存し、msx0reupのSettingボタンからbasicファイルを差し替えれば、藤田さん作のマシン語記述のエンコーダが使えて高速化が図れます。

それでも、まだまだ遅いので高速化を検討しなければなりませんね。
