from flask import g, Flask, render_template, session, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
import sqlite3
import secrets
import opencc
import numpy as np
import pandas as pd

zh_num = {1:'一', 2:'二', 3:'三', 4:'四', 5:'五', 6:'六', 7:'七', 8:'八', 9:'九', 10:'十',
          11:'十一', 12:'十二', 13:'十三', 14:'十四', 15:'十五', 16:'十六', 17:'十七', 18:'十八', 19:'十九', 20:'二十',
          21:'二十一', 22:'二十二', 23:'二十三', 24:'二十四'}

# ---- phonology ----
rc_shengxi = [
    ('共組',),
    ('求組',),
    ('但組',),
    ('傳組',),
    ('濁組',),
    ('排組',),
    ('狂組',)
    ]

rc_shengs = [
    ('共',1,'*ɡ-','ɡ'),
    ('合',1,'*ɦ-','ɦ'),
    ('呆',1,'*ŋ-','ŋ'),
    ('亨',1,'*h-','h'),
    ('按',1,'*∅-',''),
    ('果',1,'*k-','k'),
    ('康',1,'*kʰ-','kʰ'),
    ('求',2,'*dʑ-','dʑ'),
    ('諧',2,'*ɦʲ-','ɦ'),
    ('宜',2,'*ȵ-','ȵ'),
    ('曉',2,'*ɕ-','ɕ'),
    ('一',2,'*∅ʲ-',''),
    ('荊',2,'*tɕ-','tɕ'),
    ('腔',2,'*tɕʰ-','tɕʰ'),
    ('但',3,'*d-','d'),
    ('能',3,'*n-','n'),
    ('來',3,'*l-','l'),
    ('諦',3,'*t-','t'),
    ('聽',3,'*tʰ-','tʰ'),
    ('傳',4,'*dʒ-','dʒ'),
    ('授',4,'*ʒ-','ʒ'),
    ('勝',4,'*ʃ-','ʃ'),
    ('征',4,'*tʃ-','tʃ'),
    ('倡',4,'*tʃʰ-','tʃʰ'),
    ('濁',5,'*dz-','dz'),
    ('在',5,'*z-','z'),
    ('先',5,'*s-','s'),
    ('之',5,'*ts-','ts'),
    ('請',5,'*tsʰ-','tsʰ'),
    ('排',6,'*b-','b'),
    ('明',6,'*m-','m'),
    ('編',6,'*p-','p'),
    ('配',6,'*pʰ-','pʰ'),
    ('無',6,'*v-','v'),
    ('方',6,'*f-','f'),
    ('狂',7,'*ɡʷ-','ɡ'),
    ('懷',7,'*ɦʷ-','ɦ'),
    ('頑',7,'*ŋʷ-','ŋ'),
    ('況',7,'*hʷ-','h'),
    ('宛',7,'*∅ʷ-',''),
    ('光',7,'*kʷ-','k'),
    ('匡',7,'*kʰʷ-','kʰ')
    ]

rc_yunxi = [
    ('宜',),
    ('吾',),
    ('諸',),
    ('翻諧',),
    ('查',),
    ('何',),
    ('言泉',),
    ('更方',),
    ('音聲',),
    ('從',),
    ('法畫',),
    ('一得',),
    ('各俗',),
    ('隨',),
    ('要',),
    ('求',),
    ('而',)
    ]

rc_yuns = [
    ('音',9,'*in','in'),
    ('隨',14,'*ɐi','ɐi'),
    ('泉',7,'*ᴇ','ᴇ'),
    ('更',8,'*aŋ','aŋ'),
    ('何',6,'*ʊ','ʊ'),
    ('法',11,'*aʔ','aʔ'),
    ('畫',11,'*ɑʔ','ɑʔ'),
    ('一',12,'*ieʔ','ieʔ'),
    ('翻',4,'*æ','æ'),
    ('查',5,'*o','o'),
    ('諸',3,'*y','y'),
    ('聲',9,'*ən','ən'),
    ('要',15,'*ɐɯ','ɐɯ'),
    ('宜',1,'*i','i'),
    ('諧',4,'*ᴀ','ᴀ'),
    ('俗',13,'*oʔ','oʔ'),
    ('從',10,'*oŋ','oŋ'),
    ('吾',2,'*u','u'),
    ('方',8,'*ɑŋ','ɑŋ'),
    ('言',7,'*ie','ie'),
    ('求',16,'*ɤɯ','ɤɯ'),
    ('而1',17,'*l̩','l̩'),
    ('而2',17,'*ʅ','ʅ'),
    ('而3',17,'*ɿ','ɿ'),
    ('各',13,'*ɔʔ','ɔʔ'),
    ('得',12,'*əʔ','əʔ')
    ]

rc_hus = [
    ('開','',''),
    ('齊','j','i'),
    ('合','w','u'),
    ('撮','ɥ','y')
    ]

rc_tones = [
    (1,'陰平','44','꜀'),
    (1,'陽平','213','꜁'),
    (2,'陰上','53','꜂'),
    (2,'陽上','24','꜃'),
    (3,'陰去','412','꜄'),
    (3,'陽去','31','꜅'),
    (4,'陰入','4̲4̲','꜆'),
    (4,'陽入','2̲3̲','꜇')
    ]

secret = secrets.token_urlsafe(32)

db = SQLAlchemy()
app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///project.db"
app.secret_key = secret
db.init_app(app)

# Models
class ShengXi(db.Model):
    __tablename__ = 'shengxi'
    id = db.Column(db.Integer, primary_key=True)
    # 共組 求組 但組 傳組 濁組 排組 狂組
    lei = db.Column(db.String(10), unique=True)
    shengmus = db.relationship('ShengMu', backref='shengxi', lazy='dynamic')

    def __init__(self, lei):
        self.lei = lei

    def __repr__(self):
        return '<聲系 %r>' % self.lei

class ShengMu(db.Model):
    __tablename__ = 'shengmus'
    id = db.Column(db.Integer, primary_key=True)
    lei = db.Column(db.String(10), db.ForeignKey('shengxi.lei'))
    zi = db.Column(db.String(4), unique=True)
    ni = db.Column(db.String(20), unique=True)
    code = db.Column(db.String(20))
    zibiao = db.relationship('ZiBiao', backref='shengmus', lazy='dynamic')

    def __init__(self, zi, lei, ni, code):
        self.zi = zi
        self.lei = lei
        self.ni = ni
        self.code = code

    def __repr__(self):
        return '<聲母 %r>' % self.zi

class YunXi(db.Model):
    __tablename__ = 'yunxi'
    id = db.Column(db.Integer, primary_key=True)
    lei = db.Column(db.String(10), unique=True)
    yunmus = db.relationship('YunMu', backref='yunxi', lazy='dynamic')

    def __init__(self, lei):
        self.lei = lei

    def __repr__(self):
        return '<韻系 %r>' % self.lei

class SiHu(db.Model):
    __tablename__ = 'sihu'
    id = db.Column(db.Integer, primary_key=True)
    zi = db.Column(db.String(10), unique=True)
    ni = db.Column(db.String(20), unique=True)
    code = db.Column(db.String(20))
    zibiao = db.relationship('ZiBiao', backref='sihu', lazy='dynamic')

    def __init__(self, zi, ni, code):
        self.zi = zi
        self.ni = ni
        self.code = code

    def __repr__(self):
        return '<呼 %r>' % self.zi

class YunMu(db.Model):
    __tablename__ = 'yunmus'
    id = db.Column(db.Integer, primary_key=True)
    lei = db.Column(db.String(10), db.ForeignKey('yunxi.lei'))
    # if short?
    cu = db.Column(db.Boolean)
    zi = db.Column(db.String(4), unique=True)
    ni = db.Column(db.String(20), unique=True)
    code = db.Column(db.String(20))
    zibiao = db.relationship('ZiBiao', backref='yunmus', lazy='dynamic')

    def __init__(self, zi, lei, ni, code, cu):
        self.zi = zi
        self.lei = lei
        self.ni = ni
        self.code = code
        self.cu = cu

    def __repr__(self):
        return '<韻母 %r>' % self.zi

class ShengDiao(db.Model):
    __tablename__ = 'shengdiaos'
    id = db.Column(db.Integer, primary_key=True)
    lei = db.Column(db.Integer)
    yin = db.Column(db.Boolean)
    zi = db.Column(db.String(4), unique=True)
    ni = db.Column(db.String(20))
    code = db.Column(db.String(20), unique=True)
    zibiao = db.relationship('ZiBiao', backref='shengdiaos', lazy='dynamic')

    def __init__(self, lei, zi, ni, code, yin):
        self.lei = lei
        self.zi = zi
        self.ni = ni
        self.code = code
        self.yin = yin

    def __repr__(self):
        return '<聲調 %r>' % self.zi

class Book(db.Model):
    __tablename__ = 'book'
    id = db.Column(db.Integer, primary_key=True)
    # Storing path to the page image file
    path = db.Column(db.Text, unique=True)
    vol = db.Column(db.Integer)
    page = db.Column(db.Integer)
    zibiao = db.relationship('ZiBiao', backref='book', lazy='dynamic')

    def __init__(self, path, vol, page):
        self.path = path
        self.vol = vol
        self.page = page

    def __repr__(self):
        return '<頁 %r>' % self.id

class ZiBiao(db.Model):
    __tablename__ = 'zibiao'
    id = db.Column(db.Integer, primary_key=True)
    sheng_id = db.Column(db.Integer, db.ForeignKey('shengmus.id'))
    sheng = db.Column(db.String(4))
    yun_id = db.Column(db.Integer, db.ForeignKey('yunmus.id'))
    yun = db.Column(db.String(4))
    diao = db.Column(db.String(4), db.ForeignKey('shengdiaos.lei'))
    hu = db.Column(db.String(4), db.ForeignKey('sihu.zi'))
    zi = db.Column(db.String(10))
    ya = db.Column(db.String(10))
    zhu = db.Column(db.Text)
    merge = db.Column(db.Text)
    comment = db.Column(db.Text)
    page = db.Column(db.Integer, db.ForeignKey('book.id'))

    def __init__(self, sheng_id, sheng, yun_id, yun, diao, hu, zi, ya, zhu, comment, page):
        self.sheng_id = sheng_id
        self.sheng = sheng
        self.yun_id = yun_id
        self.yun = yun
        self.diao = diao
        self.hu = hu
        self.zi = zi
        self.ya = ya
        self.zhu = zhu
        self.merge = '⭗'.join([xstr(ya),xstr(zhu)]).strip('⭗')
        self.comment = comment
        self.page = page

    def __repr__(self):
        return '<字 %r>' % self.zi

# Views
@app.route('/')
def index():
    yunbu = make_cat()
    return render_template('index.html', yunbu=yunbu)

@app.route('/onsets/', methods=['GET', 'POST'])
def onsets():
    shengmu = ShengMu.query.all()
    sheng_zi = dict()
    for sheng in shengmu:
        sheng_zi[sheng.zi] = ZiBiao.query.filter_by(sheng=sheng.zi).all()
    return render_template('onsets.html', shengmu=shengmu, sheng_zi=sheng_zi)

@app.route('/onset/<int:id>', methods=['GET', 'POST'])
def onset(id):
    sheng = ShengMu.query.filter_by(id=id).first()
    return render_template('onset.html', sheng=sheng)

@app.route('/rhymes/', methods=['GET', 'POST'])
def rhymes():
    yunmu = YunMu.query.all()
    yun_zi = dict()
    for yun in yunmu:
        yun_zi[yun.zi] = ZiBiao.query.filter_by(yun=yun.zi).all()
    return render_template('rhymes.html', yunmu=yunmu, yun_zi=yun_zi)

@app.route('/rhyme/<int:id>', methods=['GET', 'POST'])
def rhyme(id):
    yun = YunMu.query.filter_by(id=id).first()
    return render_template('rhyme.html', yun=yun)

@app.route('/chars/', methods=['GET', 'POST'])
@app.route('/chars/<int:page>', methods=['GET', 'POST'])
def chars(page=1):
    yunbu = make_cat()
    zibiao = ZiBiao.query.paginate(page=page, per_page=50, error_out=False)
    return render_template('chars.html', zibiao=zibiao, yunbu=yunbu)

@app.route('/char/<int:id>', methods=['GET', 'POST'])
def char(id):
    zi = ZiBiao.query.filter_by(id=id).first()
    return render_template('char.html', zi=zi)

@app.route('/phon/')
def phon():
    sheng = ShengMu.query.all()
    yun = YunMu.query.all()
    diao = ShengDiao.query.all()
    sh_seq = [29,30,31,32,33,34,14,15,16,17,18,24,19,25,20,26,21,27,22,28,23,
              [0,35],7,[1,36],8,[2,37],9,[3,38],10,[4,39],11,[5,40],12,
              [6,41],13]
    return render_template('phon.html', sheng=sheng, yun=yun, diao=diao, sh_seq=sh_seq)

@app.route('/query/', methods=['GET', 'POST'])
def query():
    if request.method == 'POST':
        # dict of the query results
        results = {}
        yx_checked = request.form.get('yx')
        mc_checked = request.form.get('mc')
        chars = unique_char(request.form['zi'])
        key_orders = ['荆音韵汇','广韵','字','拟音','反切注音','声纽','韵部','声调','四呼','注释']

        if yx_checked:
            entries = []
            for char in chars:
                for entry in ZiBiao.query.filter_by(zi=char).all():
                    yx_dict = {}
                    yx_dict['字'] = entry.zi
                    if ShengDiao.query.filter_by(zi=entry.diao).first().lei < 3:
                        yx_dict['拟音'] = merge_repeated(
                            ShengDiao.query.filter_by(zi=entry.diao).first().code+
                            ShengMu.query.filter_by(zi=entry.sheng).first().code+
                            SiHu.query.filter_by(zi=entry.hu).first().code+
                            YunMu.query.filter_by(zi=entry.yun).first().code
                            )
                    else:
                        yx_dict['拟音'] = merge_repeated(
                            ShengMu.query.filter_by(zi=entry.sheng).first().code+
                            SiHu.query.filter_by(zi=entry.hu).first().code+
                            YunMu.query.filter_by(zi=entry.yun).first().code+
                            ShengDiao.query.filter_by(zi=entry.diao).first().code
                            )
                    yx_dict['声纽'] = entry.sheng
                    yx_dict['韵部'] = entry.yun
                    yx_dict['声调'] = entry.diao
                    yx_dict['四呼'] = entry.hu
                    yx_dict['注释'] = entry.merge
                    entries.append(dict2list(yx_dict, key_orders))
            results['荆音韵汇'] = entries
        if mc_checked:
            entries = []
            for char in chars:
                for entry in query_db('select * from mc_char where 字頭 = ?', char):
                    mc_dict = {}
                    mc_dict['字'] = entry['字頭']
                    mc_dict['反切注音'] = entry['字音']
                    mc_dict['注释'] = entry['釋義']+'◎'+entry['補釋']
                    entries.append(dict2list(mc_dict, key_orders))
            results['广韵'] = entries

        session['results'] = dict2list(results, key_orders)
        session['yx_chk'] = True if yx_checked else False
        session['mc_chk'] = True if mc_checked else False
        return redirect(url_for('query'))
    return render_template('query.html')

@app.route('/table/')
def table(data=None):
    # make rhime tables
    csv_path = 'scripts/tables/'
    all_data = pd.DataFrame()
    temp_data = pd.DataFrame()
    for page in range(1,21):
        csv_file = csv_path + 'table-' + str(page) + '.csv'
        temp_data = pd.read_csv(csv_file, delimiter=' ', na_values='', encoding='utf-8').T
        if page == 1:
            all_data = temp_data
        else:
            all_data = pd.concat([all_data, temp_data.iloc[1:]], axis = 0)
    shengniu = all_data.iloc[0,:][2:]
    all_data.insert(0, '韻部', [item[0] for item in all_data.index])
    all_data.columns = ['韻部', '四呼', '聲調'] + list(shengniu)
    all_data = all_data.reset_index(drop=True)
    all_data = all_data.drop(all_data.index[[0]])
    return render_template('table.html',
        data=all_data.to_html(index=False,
                              classes=['table','table-bordered','table-condensed']))

@app.route('/events/')
def events():
    return render_template('events.html')

@app.route('/book/')
def book():
    return render_template('book.html')

@app.route('/maps/')
def maps():
    return render_template('maps.html')

# Helper
def merge_repeated(s):
    """
    merging repeated string
    """
    import itertools
    ns = ''.join(ch for ch, _ in itertools.groupby(s))
    return ns

def unique_char(s):
    converter = opencc.OpenCC('s2t')
    s = converter.convert(s)
    seen = set()
    seen_add = seen.add
    return [x for x in s if not (x in seen or seen_add(x))]

def dict2list(d, keys):
    """
    dict to ordered list
    """
    li = []
    for k in keys:
        if k in d.keys():
            li.append((k,d[k]))
    return li

def make_cat():
    """
    make a catelog for yuns
    """
    yun_cat = []
    count = 1
    for item in rc_yuns:
        yun = item[0]
        if yun == '而2' or yun == '而3':
            continue
        else:
            yun_cat.append(
                (
                    zh_num[count],
                    yun[0],
                    ZiBiao.query.filter_by(yun=yun).first().id
                )
            )
            count += 1
    return yun_cat

def connect_db():
    rv = sqlite3.connect(app.config['SQLALCHEMY_DATABASE_URI'])
    rv.row_factory = sqlite3.Row
    return rv

def get_db():
    if not hasattr(g, 'sqlite_db'):
        g.sqlite_db = connect_db()
    return g.sqlite_db

def xstr(s):
    return '' if s is np.nan else str(s)

@app.teardown_appcontext
def close_db(error):
    """Closes the database again at the end of the request."""
    if hasattr(g, 'sqlite_db'):
        g.sqlite_db.close()

def query_db(query, args=(), one=False):
    cur = get_db().execute(query, args)
    rv = cur.fetchall()
    cur.close()
    return (rv[0] if rv else None) if one else rv

if __name__ == '__main__':
    with app.app_context():
        db.create_all()

    app.run()
