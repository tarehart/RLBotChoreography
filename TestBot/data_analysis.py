import numpy as np
import matplotlib.pyplot as plt

# For drift
'''
for test in range(0,330):
    # Removing anomalies.
    if test not in [19,80,282,310]:
        # Loading data.
        data = np.load(f'D:/RLBot/ViliamVadocz/TestBot/data/test_{test:03}.npy')
        # Selection position data.
        pos = data[0]
        # Transforming to start from origin and to be the correct way around (reverse x-axis).
        pos += np.array([-2500, 2300, -17.01])
        pos *= np.array([-1, 1, 1])
        # Plotting trace.
        plt.plot(pos[:,0],pos[:,1])

# Showing plotted paths.   
plt.show()
'''

# Distance - time esimation.
for test in [3, 5, 7, 9]:
    # Loading data.
    data = np.load(f'D:/RLBot/ViliamVadocz/TestBot/data/test_{test:02}.npy')
    # Selection position data.
    times = data[0]
    distances = data[1]
    # Plotting trace.
    plt.plot(distances, times)

# Hand-fitted graph.
x = np.linspace(0, 3000, 100)
y = x**0.55 / 41.53
y[x>2177.25] = 1/2300 * x[x>2177.25] + 0.70337
plt.plot(x, y)

# Showing plotted paths.
plt.show()
