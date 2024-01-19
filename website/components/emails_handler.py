#from flask_postmark import Postmark
#
#app = Flask(__name__)
#app.config["POSTMARK_SERVER_TOKEN"] = "3064a316-c492-499f-b418-c10ff91df1f7"
#
#postmark = Postmark(app)
#
#
#@app.route("/send", methods=["POST"])
#def send():
#    postmark.send(
#        From="test@facilitybooker.com",
#        To="domisku123@gmail.com",
#        Subject="Postmark facility booking test",
#        HtmlBody="<html><body><strong>Hello</strong> Saiikowski.</body></html>",
#    )
#    return b"OK"
#
#send()