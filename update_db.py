@app.route('/alerts')
def alerts():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM alerts")
    data = cur.fetchall()
    conn.close()

    return render_template('alerts.html', alerts=data)