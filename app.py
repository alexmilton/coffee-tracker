from flask import Flask, abort, render_template, request, redirect, url_for
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

    # Pagination: 25 per page
    page = request.args.get('page', 1, type=int)
    purchasesPagination = CoffeePurchase.query.order_by(
        CoffeePurchase.purchaseDate.desc(),
        CoffeePurchase.id.desc()
    ).paginate(page=page, per_page=25, error_out=False)

    roasters = [r[0] for r in db.session.query(func.distinct(CoffeePurchase.roaster)).order_by(CoffeePurchase.roaster).all()]
    coffees = [c[0] for c in db.session.query(func.distinct(CoffeePurchase.coffeeName)).order_by(CoffeePurchase.coffeeName).all()]

    # All Time Stats
    totalBagsAllTime = CoffeePurchase.query.count()
    totalGramsAllTime = db.session.query(func.coalesce(func.sum(CoffeePurchase.bagWeightGrams), 0)).scalar()
    totalSpendAllTime = db.session.query(func.coalesce(func.sum(CoffeePurchase.cost), 0)).scalar()
    avgCostPer100GramsAllTime = round(totalSpendAllTime / totalGramsAllTime * 100, 4) if totalGramsAllTime > 0 else 0.0

    # Current Year Stats
    currentYear = datetime.now().year
    startOfYear = date(currentYear, 1, 1)

    totalBagsYear = db.session.query(CoffeePurchase).filter(CoffeePurchase.purchaseDate >= startOfYear).count()
    totalGramsYear = db.session.query(func.coalesce(func.sum(CoffeePurchase.bagWeightGrams), 0)).filter(CoffeePurchase.purchaseDate >= startOfYear).scalar()
    totalSpendYear = db.session.query(func.coalesce(func.sum(CoffeePurchase.cost), 0)).filter(CoffeePurchase.purchaseDate >= startOfYear).scalar()
    avgCostPer100GramsYear = round(totalSpendYear / totalGramsYear * 100, 4) if totalGramsYear > 0 else 0.0

    stats = {
        'allTime': {
            'totalBags': totalBagsAllTime,
            'totalSpend': round(totalSpendAllTime, 2),
            'avgCostPer100Grams': avgCostPer100GramsAllTime
        },
        'currentYear': {
            'year': currentYear,
            'totalBags': totalBagsYear,
            'totalSpend': round(totalSpendYear, 2),
            'avgCostPer100Grams': avgCostPer100GramsYear
        }
    }

    return render_template(
        'index.html',
        purchasesPagination=purchasesPagination,
        roasters=roasters,
        coffees=coffees,
        stats=stats
    )

@app.post('/purchase/<int:purchase_id>/edit')
def edit_purchase(purchase_id):
    purchase = db.get_or_404(CoffeePurchase, purchase_id)
    purchaseDateStr = request.form.get('purchaseDate', '').strip()
    roasterVal = request.form.get('roaster', '').strip()
    coffeeNameVal = request.form.get('coffeeName', '').strip()
    bagWeightVal = request.form.get('bagWeightGrams', '').strip()
    costVal = request.form.get('cost', '').strip()

    try:
        purchaseDate = datetime.strptime(purchaseDateStr, '%Y-%m-%d').date()
        bagWeightGrams = float(bagWeightVal)
        cost = float(costVal)
    except (TypeError, ValueError):
        abort(400, description='Enter a valid date, size, and cost.')

    if not roasterVal or not coffeeNameVal or bagWeightGrams <= 0 or cost < 0:
        abort(400, description='Enter a roaster, coffee name, positive size, and non-negative cost.')

    purchase.purchaseDate = purchaseDate
    purchase.roaster = roasterVal
    purchase.coffeeName = coffeeNameVal
    purchase.bagWeightGrams = bagWeightGrams
    purchase.cost = cost
    db.session.commit()

    page = request.form.get('page', 1, type=int)
    return redirect(url_for('index', page=page))

@app.post('/purchase/<int:purchase_id>/delete')
def delete_purchase(purchase_id):
    purchase = db.get_or_404(CoffeePurchase, purchase_id)
    db.session.delete(purchase)
    db.session.commit()

    page = request.form.get('page', 1, type=int)
    return redirect(url_for('index', page=page))

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

    # Roaster Summary Breakdown: distinct order dates, bag count, spend, avg cost/bag, avg cost/100g
    roasterStatsQuery = db.session.query(
        CoffeePurchase.roaster,
        func.count(func.distinct(CoffeePurchase.purchaseDate)).label('orderCount'),
        func.count(CoffeePurchase.id).label('bagCount'),
        func.sum(CoffeePurchase.cost).label('totalSpend'),
        func.avg(CoffeePurchase.cost).label('avgCostPerBag'),
        (func.sum(CoffeePurchase.cost) / func.sum(CoffeePurchase.bagWeightGrams) * 100).label('avgCostPer100Grams')
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