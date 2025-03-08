## Reflection

This dashboard is designed to assist the Canadian government by analyzing commuting patterns, focusing on transportation modes and commute times. It aims to identify trends that can inform national policies.

The following image displays the original proposal from Milestone 1: 

!["Dashboard - Milestone 1"](../img/sketch.png)

The image below displays the current state of the *Commuting Insights* app relative to the status at the time of Milestone 2 delivery.

!["Dashboard - Milestone 3"](../img/sketch_m3.png)

### Implemented Features

- Line plot for `Average Commute Time` vs `Time Arriving at Work`.
- Addition of styling features such as using cards to contain widgets to define sample, adding padding to app, as well as updates to titles, labels, and axis. 
- Browser title bar displaying app name. 
- Addition of footer with app description and relevant links.
- Discrepancies between displayed `Average Commute Time` and `Weighted Average Commute Time` have been resolved.
- Significant upates to bar plot and violin plots for interpretability (i.e. legends, axis swapping).
- Updated preprocessing of dataset for improved performance and removal of unused examples.

### Missing Features

- There are no missing features from plan.

### Changes to proposal

- Scatter plot for `Average Commute Time` vs `Total Commute Observations`, while present in the Original sketch and Milestone 2's missing features, has been removed from plan given its redundancy with the information contained in other plots.

These changes have minimal impact on the app's intended purpose while reducing code complexity and visual clutter.

### Issues

- While the app deployment is fully functional, it experiences performance issues on the `render.com` platform, causing slower display times.

### Best Practice Deviations 

- None identified.

### Summary

- Strengths: The completed app aligns with expectations, follows best practices and has a well-structured layout.
- Strengths: Improved data preprocessing enabled consistently successful rendering of the app.
- Limitations: While the app is functional running locally and on Render, responsiveness is slow on Render and update times are long.
- Future Improvement: The scatter plot could display `Commuting Density` on the x-axis instead of `Total Commute Observations`. Since `area` data is not available to calculate `Commuting Density`, the improvement would involve finding and incorporating it into the dataset.
- Future Improvement: The app could be improved by recovering geographical categorization by `Province` to align to the availability of commute data.