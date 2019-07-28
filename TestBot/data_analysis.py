import numpy as np
import matplotlib.pyplot as plt

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