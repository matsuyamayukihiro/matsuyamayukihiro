from flask import Flask, render_template, request, session, redirect, url_for, jsonify
# from sqlalchemy.sql.base import ColumnCollection
# from sqlalchemy import or_, desc
from models.models import *
from models.database import db_session
from datetime import datetime
from app import key
from hashlib import sha256
import logging

logging.basicConfig()
logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)
app = Flask(__name__)
app.secret_key = key.SECRET_KEY
app.config['JSON_AS_ASCII'] = False  # 日本語を使えるように


# ログイン系
@app.route("/login", methods=["post"])  # ログイン機能
def login():
    user_name = request.form["user_name"]  # フォームに入力されたユーザ名を取得
    user = User.query.filter_by(user_name=user_name).first()  # そのユーザ名を持つDBレコードをusersテーブルから抽出しています
    if user:  # 入力された名前がDBより抽出した時
        password = request.form["password"]
        hashed_password = sha256((user_name + password + key.SALT).encode("utf-8")).hexdigest()
        if user.hashed_password == hashed_password:  # DB内のパス = 入力されたパスがという構図
            session["user_name"] = user_name  # セッション情報にユーザ名を追加
            return redirect(url_for("index"))  # メインページへ遷移
        else:
            return redirect(url_for("top", status="wrong_password"))
    else:
        return redirect(url_for("top", status="user_notfound"))


@app.route("/newcomer")  # 新規登録機能
def newcomer():
    status = request.args.get("status")
    return render_template("newcomer.html", status=status)


@app.route("/registar", methods=["post"])  # 新規登録機能
def registar():
    user_name = request.form["user_name"]  # ユーザ名orメアド登録も可能
    user = User.query.filter_by(user_name=user_name).first()
    if user:
        return redirect(url_for("newcomer", status="exist_user"))
    else:
        password = request.form["password"]  # 入力されたパスワードの取得
        hashed_password = sha256((user_name + password + key.SALT).encode("utf-8")).hexdigest()  # 暗号化している
        user = User(user_name, hashed_password)
        db_session.add(user)  # DBに追加(userクラス)　
        db_session.commit()  # DBに反映
        session["user_name"] = user_name  # セッション情報にユーザ名を追加
        return redirect(url_for("index"))  # メインページへ遷移


@app.route("/logout")
def logout():
    session.pop("user_name", None)
    return redirect(url_for("top", status="logout"))


# トップページ系
@app.route("/")
@app.route("/index")
def index():  # トップページ開く
    if "user_name" in session:
        name = session["user_name"]
        all_onegai = OnegaiContent.query.all()
        return render_template("index.html", name=name, all_onegai=all_onegai)
    else:
        return redirect(url_for("top", status="logout"))


# コラム系
@app.route("/column")  # コラム表示機能
def column():
    query = db_session.query(Columns)
    columns = query.all()
    count = query.count()

    list_column = {}
    for i, row in enumerate(columns):
        list_column["column" + str(i)] = row.toDict()

    list_column["count"] = count
    return jsonify(list_column)


# アイデア出し系
@app.route("/idea")  # アイデア表示
def idea():  # 投稿アイデア表示機能
    query = db_session.query(Ideas)
    ideas = query.all()  # データ抽出
    counter = query.\
        filter(Ideas.idea_id == Good_ideas.good_idea_id).\
        all()

    # -データ個数カウント
    list_idea = {}
    for s, row1 in enumerate(ideas):
        list_idea["idea" + str(s)] = row1.toDict2()

    return jsonify(list_idea)


# いいね機能
def good_add():  # 投稿アイデア表示機能
    good_idea_id = request.form["request_idea_id"]  # いいねリクエストした対象投稿idデータ取得
    good_idea_userid = request.form["request_idea_userid"]  # いいねリクエストしたユーザidデータ取得
    good_idea_date = request.form["request_date_id"]  # いいねリクエストした日時データ取得

    # いいねした人idといいねされた対象投稿のidを連結したテーブル
    if good_idea_userid == Good_ideas.good_idea_userid:
        if good_idea_id == Good_ideas.good_idea_id:
            db_session.query(Good_ideas).\
                filter(good_idea_id == Good_ideas.good_idea_id).\
                delete()

    else:  # リストに名前が無かったら
        good_add = Good_ideas(good_idea_id = good_idea_id , good_idea_userid = good_idea_userid, good_idea_date = good_idea_date)
        db_session.add(good_add)

    db_session.commit
#    db_session.add(good_person)  # 引数は追加したい変数
#   db_session.commit()  # 追加データの反映


@app.route("/add", methods=["post"])
def add():  # データベース内の各項目に入力値の追加
    title = request.form["title"]  # HTML内のデータ取得
    body = request.form["body"]
    content = OnegaiContent(title, body, datetime.now())  # OnegaiContent=データ追加（引数は追加したいデータ）
    db_session.add(content)  # 引数は追加したい変数
    db_session.commit()  # 追加データの反映
    return redirect(url_for("index"))


@app.route("/update", methods=["post"])
def update():
    content = OnegaiContent.query.filter_by(id=request.form["update"]).first()
    content.title = request.form["title"]
    content.body = request.form["body"]
    db_session.commit()
    return redirect(url_for("index"))


@app.route("/delete", methods=["post"])
def delete():
    id_list = request.form.getlist("delete")
    for id in id_list:
        content = OnegaiContent.query.filter_by(id=id).first()
        db_session.delete(content)
    db_session.commit()
    return redirect(url_for("index"))


@app.route("/top")
def top():
    status = request.args.get("status")
    return render_template("top.html", status=status)


if __name__ == "__main__":
    app.run(debug=True)