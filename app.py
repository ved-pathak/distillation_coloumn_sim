from flask import Flask, request, jsonify, render_template
from compute_engine import compute_engine 
import random
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
app = Flask(__name__)

@app.route("/")
def index():
    return render_template("index.html")  

@app.route('/simulate', methods=['POST'])
def simulate():
    try:
        data = request.get_json()

        # Logging incoming data
        print("[INFO] Received data:", data)

        # Extract and validate input data
        feed_rate = data.get('feed_rate')
        feed_ratev = data.get('feed_rate')+random.uniform(-4,4)
       
        feed_composition = data.get('feed_composition')  # Should be a list of floats
        q = data.get('q')

        temperature = data.get('temperature')
        temperaturev = data.get('temperature') + random.uniform(-2.0, 2.0)
        distillate_purity = data.get('distillate_purity')
        distillate_purityv = data.get('distillate_purity')+random.uniform(-0.02, 0.02)

        # Check required fields
        if None in (feed_rate, feed_composition, q, temperature, distillate_purity):
            return jsonify({"error": "Missing required input fields."}), 400

        # Antoine constants for vapor pressure calculation 
        antoine_constants = ([
            [8.07, 1730.63, 233.426],
            [7.96, 1668.21, 228.0],
            [7.52, 1554.679, 240.337],
            [7.11, 1344.8, 219.48]
        ])


        # Call core computation engine for simulation
        result = compute_engine(
            F=feed_ratev,
            Z=feed_composition,  
            T=temperaturev,
            q=q,
            xD2=distillate_purityv,
            antoine_constants=antoine_constants
        )
        result1 = compute_engine(
            F=feed_rate,
            Z=feed_composition,  
            T=temperature,
            q=q,
            xD2=distillate_purity,
            antoine_constants=antoine_constants
        )
        # Data#####
        labels = ['refinery gas', 'Gasoline', 'Kerosene', 'Diesel']
        sizes = result1["Distillate Composition"]  # Percentages or values
        colors = ['#ff9999','#66b3ff','#99ff99','#ffcc99']  # Optional

        # Plot
        plt.figure(figsize=(6,6))
        plt.pie(sizes, labels=labels, colors=colors, autopct='%1.1f%%', startangle=90)
        plt.title('Distillate Composition')
        plt.axis('equal')  # Equal aspect ratio ensures the pie chart is a circle.
        plt.savefig('static/distillate.png', dpi=300, bbox_inches='tight')  # dpi=300 for high quality
        plt.close()
        #2-pie chart for bottom composition
        labels = ['refinery gas', 'Gasoline', 'Kerosene', 'Diesel']
        sizes = result1["Bottom Composition"]  # Percentages or values
        colors = ['#ff9999','#66b3ff','#99ff99','#ffcc99']  # Optional

        # Plot
        plt.figure(figsize=(6,6))
        plt.pie(sizes, labels=labels, colors=colors, autopct='%1.1f%%', startangle=90)
        plt.title('Bottom Composition')
        plt.axis('equal')  # Equal aspect ratio ensures the pie chart is a circle.
        plt.savefig('static/bottom.png', dpi=300, bbox_inches='tight')  # dpi=300 for high quality
        plt.close()
        #N min vs purity of gasoline 0.5 to 1
        purity=[]
        Nmin=[]
        Rmin=[]
        for i in range(50):
            p=(i+50)/100
            purity.append(p)

            res = compute_engine(
            F=feed_rate,
            Z=feed_composition,  
            T=temperature,
            q=q,
            xD2=p,#distillate_purity,
            antoine_constants=antoine_constants
            )
            n=res["Minimum Theoretical Stages (Fenske)"]
            r=res["Minimum Reflux Ratio (Underwood)"]
            Nmin.append(n)
            Rmin.append(r)
        # Plot nmin vs purity graph
        plt.figure(figsize=(6, 4))
        plt.plot(purity, Nmin, marker='o', color='blue', label='Graph 1')
        plt.xlabel("Purity of gasoline")
        plt.ylabel("minimum no. of stages")
        plt.title("nmin vs purity graph")
        plt.grid(True)
        plt.legend()
        plt.savefig("static/Nmin.png", dpi=300, bbox_inches='tight')
        plt.close()  # Close the figure to free memory
        # Plot Rmin vs Purity  graph
        plt.figure(figsize=(6, 4))
        plt.plot(purity, Rmin, marker='s', color='green', label='Graph 2')
        plt.xlabel("Purity of gasoline")
        plt.ylabel("Min reflux ratio")
        plt.title("Rmin vs Purity  graph")
        plt.grid(True)
        plt.legend()
        plt.savefig("static/Rmin.png", dpi=300, bbox_inches='tight')
        plt.close()
        return jsonify(result)

    except Exception as e:
        print("[ERROR] Simulation failed:", str(e))
        return jsonify({"error": "Simulation failed.", "details": str(e)}), 500
@app.route("/graphs", methods=['GET'])
def graphs():
    return render_template("graphs.html")



if __name__ == "__main__":
    app.run(debug=True)
