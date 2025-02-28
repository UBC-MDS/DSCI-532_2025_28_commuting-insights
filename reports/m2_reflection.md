## Milestone 2 Reflection

This dashboard aims to assist the Canadian government by comparing commuting patterns, focusing on transportation modes and commute times to identify trends for informing national policies.

The image below displays the original *Commuting Insights* sketch proposal and its status at the time of Milestone 2 delivery.

!["Dashboard - Milestone 2"](../img/sketch_m2.png)

### Implemented Features:

The current version of the app includes the following features:

- Choropleth map focused on `Census Division` in Canada, colored by `Average Commute Time`.
- Drop-down filter to select `Census Division` of interest in Canada.
- Drop-down filter to select one or multiple commuting modes to define the data sample.
- Slider to filter data based on `Arrival Time`.
- Violin plot for `Average Commute Time` vs selected `Commuting Mode`. Plot displays values of selected `Census Division`.
- Scatter plot for `Average Commute Time` vs `Total Commute Time`.
- Choropleth and descriptive visualizations respond to data filters.

### Missing Features:

- Line plot for `Average Commute Time` by `Time of Day`.
- Styling features have not been developed.

### Changes to proposal

- The radio button for selecting the type of regional division has been removed, focusing only on `Census Division`. Divisions by `Province` and `Census Sub-Divisions` were excluded because `Census Sub-divisions` lacked quality for proper display on the choropleth map.
- The individual dropdown widgets for selecting individual reference `census regions` have been replaced by a single dropdown for selecting the `census region` of interest.
- The bar chart displaying the proportion of commute counts by Commute Time Range has been removed, as its insights were redundant with the violin plots.
- The layout has been restructured: the sample selection section at the top, the choropleth map on the middle left, and descriptive visualizations on the bottom and right.

These changes have minimal impact on the app's intended purpose while reducing code complexity and visual clutter.

### Issues

- The choropleth map reads average commute times directly from the dataset, while other charts calculate a weighted average based on the number of observations. This discrepancy will be addressed in future iterations.
- The browser title bar currently displays only "Dash" and should reflect the app’s name

### Best Practice Deviations 

- Outlier management in the data sample makes plots difficult to interpret, as the visualization areas are consumed by outliers. This issue is being addressed for future iterations.

### Strengths, Limitations, Potential Future Improvements

- Strengths: The app is responsive, aligns with expectations, and follows best practices. It has a well-structured layout.
- Limitations: The app could be improved stylistically to enhance visual appeal.
- Limitations: While performance is adequate locally, Render responsiveness is slow to updates.
- Future Improvement: The scatter plot could display `Commuting Density` on the x-axis instead of `Total Commute Observations`. Since `area` data is not available to calculate `Commuting Density`, the improvement would involve finding and incorporating it into the dataset.
- Future Improvement: The app could be improved by recovering geographical categorization by `Province` to align to the availability of commute data.