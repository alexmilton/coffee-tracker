from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func, desc
from datetime import datetime, date

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
        purchaseDateStr = request.form['purchaseDate'].strip()
        roasterVal = request.form['roaster'].strip()

        coffeeNames = request.form.getlist('coffeeName')
        bagWeights = request.form.getlist('bagWeightGrams')
        costs = request.form.getlist('cost')

        for i in range(len(coffeeNames)):
            cName = coffeeNames[i].strip()
            if cName and bagWeights[i] and costs[i]:
                newPurchase = CoffeePurchase(
                    purchaseDate=datetime.strptime(purchaseDateStr, '%Y-%m-%d').date(),
                    roaster=roasterVal,
                    coffeeName=cName,
                    bagWeightGrams=float(bagWeights[i]),
                    cost=float(costs[i])
                )
                db.session.add(newPurchase)

        db.session.commit()
        return redirect(url_for('index'))

    # Pagination: 50 per page
    page = request.args.get('page', 1, type=int)
    purchasesPagination = CoffeePurchase.query.order_by(
        CoffeePurchase.purchaseDate.desc(),
        CoffeePurchase.id.desc()
    ).paginate(page=page, per_page=50, error_out=False)

    roasters = [r[0] for r in db.session.query(func.distinct(CoffeePurchase.roaster)).order_by(CoffeePurchase.roaster).all()]
    coffees = [c[0] for c in db.session.query(func.distinct(CoffeePurchase.coffeeName)).order_by(CoffeePurchase.coffeeName).all()]

    # All Time Stats
    totalBagsAllTime = CoffeePurchase.query.count()
    totalGramsAllTime = db.session.query(func.coalesce(func.sum(CoffeePurchase.bagWeightGrams), 0)).scalar()
    totalSpendAllTime = db.session.query(func.coalesce(func.sum(CoffeePurchase.cost), 0)).scalar()
    avgCostPerGramAllTime = round(totalSpendAllTime / totalGramsAllTime, 4) if totalGramsAllTime > 0 else 0.0

    # Current Year Stats
    currentYear = datetime.now().year
    startOfYear = date(currentYear, 1, 1)

    totalBagsYear = db.session.query(CoffeePurchase).filter(CoffeePurchase.purchaseDate >= startOfYear).count()
    totalGramsYear = db.session.query(func.coalesce(func.sum(CoffeePurchase.bagWeightGrams), 0)).filter(CoffeePurchase.purchaseDate >= startOfYear).scalar()
    totalSpendYear = db.session.query(func.coalesce(func.sum(CoffeePurchase.cost), 0)).filter(CoffeePurchase.purchaseDate >= startOfYear).scalar()
    avgCostPerGramYear = round(totalSpendYear / totalGramsYear, 4) if totalGramsYear > 0 else 0.0

    stats = {
        'allTime': {
            'totalBags': totalBagsAllTime,
            'totalSpend': round(totalSpendAllTime, 2),
            'avgCostPerGram': avgCostPerGramAllTime
        },
        'currentYear': {
            'year': currentYear,
            'totalBags': totalBagsYear,
            'totalSpend': round(totalSpendYear, 2),
            'avgCostPerGram': avgCostPerGramYear
        }
    }

    return render_template(
        'index.html',
        purchasesPagination=purchasesPagination,
        roasters=roasters,
        coffees=coffees,
        stats=stats
    )

@app.route('/stats')
def stats_detail():
    # Top 5 Roasters by Bag Count
    topRoasters = db.session.query(
        CoffeePurchase.roaster,
        func.count(CoffeePurchase.id).label('bagCount')
    ).group_by(CoffeePurchase.roaster).order_by(desc('bagCount')).limit(5).all()

    # Top 5 Coffees by Bag Count
    topCoffees = db.session.query(
        CoffeePurchase.coffeeName,
        CoffeePurchase.roaster,
        func.count(CoffeePurchase.id).label('bagCount')
    ).group_by(CoffeePurchase.coffeeName, CoffeePurchase.roaster).order_by(desc('bagCount')).limit(5).all()

    # Roaster Summary Breakdown: distinct order dates, bag count, spend, avg cost/bag, avg cost/g
    roasterStatsQuery = db.session.query(
        CoffeePurchase.roaster,
        func.count(func.distinct(CoffeePurchase.purchaseDate)).label('orderCount'),
        func.count(CoffeePurchase.id).label('bagCount'),
        func.sum(CoffeePurchase.cost).label('totalSpend'),
        func.avg(CoffeePurchase.cost).label('avgCostPerBag'),
        (func.sum(CoffeePurchase.cost) / func.sum(CoffeePurchase.bagWeightGrams)).label('avgCostPerGram')
    ).group_by(CoffeePurchase.roaster).order_by(desc('bagCount')).all()

    totalUniqueRoasters = len(roasterStatsQuery)
    totalUniqueCoffees = db.session.query(func.count(func.distinct(CoffeePurchase.coffeeName))).scalar() or 0

    return render_template(
        'stats.html',
        topRoasters=topRoasters,
        topCoffees=topCoffees,
        roasterStats=roasterStatsQuery,
        totalUniqueRoasters=totalUniqueRoasters,
        totalUniqueCoffees=totalUniqueCoffees
    )

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)