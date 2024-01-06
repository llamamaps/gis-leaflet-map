from flask import Flask, render_template, request, make_response
import psycopg2, os, jinja2, json

app = Flask(__name__, static_url_path='/static')

def get_db_connection():
    conn = psycopg2.connect(host='localhost',
                            database='hawaii',
                            user=os.environ['PGUSER'],
                            password=os.environ['PGPASSWORD'])
    return conn

@app.route("/")
def index():
    return app.send_static_file('index.html')
@app.route("/search")
def search():
    place = request.args.get('term')
       # This adds a `%` to the end of the `place` parameter, changing, e.g. "Hono" to "Hono%".
    place = "{}{}{}".format('%',place,'%') 
    # Get a Database connection to the OSM database
    conn = get_db_connection()

    # cursor() allows python code to execute SQL in the database
    cur = conn.cursor()
    
    # This is the actual query. You may want to work out the SQL statement in a separate `psql` or other datbase session.
    # The start SQL will give you everything matching `place` exactly which isn't quite what you need. 
    # See the instructions for guidance on how to update this for this jquery autocomplete
    sql = '''
SELECT 
    concat(name, ' (', type, ')') as label,
    name, 
    st_x(st_transform(geometry,4326)) as lon,
    st_y(st_transform(geometry,4326)) as lat
FROM 
  import.osm_places 
WHERE 
  upper(name) LIKE upper(%s);
'''
    cur.execute(sql, [place])

    # For our pursposes we want to save the results in a special json format with two keys: `label` and `value`.
    # That's because jquery `autocomplete` will work if follow this format convention for our JSON output.

    results = []
    for row in cur.fetchall():
        results.append(
             { 
                 'label': row[0],
                 'value': row[1],
                  'lon': row[2], 
                  'lat': row[3], 
                  } 
                  )
    cur.close()
    conn.close()

    # This converts our list of dicts into an HTML-friendly format for our http response
    template = jinja2.Template("""{{ matches | tojson(indent=2) }}""")
    return template.render(matches=results)

@app.route("/find_coffee")
def find_coffee():
    lon = request.args.get('lon')
    lat = request.args.get('lat')

    conn = get_db_connection()
    cur = conn.cursor()
    ewkt = "SRID=4326;POINT("+lon+" "+lat+")"
    sql = '''
SELECT 
  a.geometry <-> ST_Transform(%s::geometry,3857) AS dist, 
  osm_id, 
  name,
  ST_Y(ST_Transform(ST_Centroid(a.geometry), 4326)) AS lat,
  ST_X(ST_Transform(ST_Centroid(a.geometry), 4326)) AS lon
FROM
  import.osm_amenities a
WHERE
  type='cafe'
ORDER BY
  dist
LIMIT 5;
'''
    cur.execute(sql, [ewkt])

    results = []
    for row in cur.fetchall():
        results.append({'dist': row[0], 'osm_id': row[1], 'name': row[2], 'lat': row[3], 'lon': row[4]})
    cur.close()
    conn.close()
    template = jinja2.Template("""{{ matches | tojson(indent=2) }}""")
    return template.render(matches=results)
if __name__ == "__main__":
    app.run(host='0.0.0.0')