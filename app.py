from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func
from datetime import datetime

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////data/coffee.db'
db = SQLAlchemy(app)

class CoffeePurchase(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    purchaseDate = db.Column(db.Date, nullable=False, default=datetime.utcnow)
    roaster = db.Column(db.String(120), nullable=False)
    coffeeName = db.Column(db.String(120), nullable=False)
    bagWeightGrams = db.Column(db.Float, nullable=False)
    cost = db.Column(db.Float, nullable=False)

with app.app_context():
    db.create_all()

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        newPurchase = CoffeePurchase(
            purchaseDate=datetime.strptime(request.form['purchaseDate'], '%Y-%m-%d').date(),
            roaster=request.form['roaster'].strip(),
            coffeeName=request.form['coffeeName'].strip(),
            bagWeightGrams=float(request.form['bagWeightGrams']),
            cost=float(request.form['cost'])
        )
        db.session.add(newPurchase)
        db.session.commit()
        return redirect(url_for('index'))

    purchases = CoffeePurchase.query.order_by(CoffeePurchase.purchaseDate.desc()).all()
    roasters = [r[0] for r in db.session.query(func.distinct(CoffeePurchase.roaster)).all()]
    coffees = [c[0] for c in db.session.query(func.distinct(CoffeePurchase.coffeeName)).all()]
    
    totalBags = CoffeePurchase.query.count()
    totalGrams = db.session.query(func.coalesce(func.sum(CoffeePurchase.bagWeightGrams), 0)).scalar()
    totalSpend = db.session.query(func.coalesce(func.sum(CoffeePurchase.cost), 0)).scalar()
    
    avgCostPerGram = round(totalSpend / totalGrams, 4) if totalGrams > 0 else 0.0

    stats = {
        'totalBags': totalBags,
        'totalSpend': round(totalSpend, 2),
        'avgCostPerGram': avgCostPerGram
    }

    return render_template('index.html', purchases=purchases, roasters=roasters, coffees=coffees, stats=stats)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)