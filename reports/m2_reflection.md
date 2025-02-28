## Milestone 2 Reflection

The purpose of this project is to assist the Canadian federal government by providing a comprehensive comparison of commuting patterns across Canada. This application will focus on the relationship between transportation modes and commute times, identifying trends that can inform national transportation policies.

The following image displays the original *Commuting Insights* sketch proposal and its status at the time of Milestone 2 delivery.

!["Dashboard - Milestone 2"](../img/sketch_m2.png)

### What has been implemented?

The current version of the app includes the following features:

- Choropleth map focused on `Census Division` in Canada, colored by `Average Commute Time`.
- Drop-down filter to select `Census Division` of interest in Canada.
- Drop-down filter to select one or multiple commuting modes to define the data sample.
- Slider to filter data based on `Arrival Time` of the commute.
- Violit plot for `Average Commute Time` vs selected `Commuting Mode`. Plot displays the specific values of selected `Census Division`.
- Scatter plot for `Average Commute Time` vs `Total Census Records`.
- Choropleth and descriptive visualizations are responsive to data filters.
- App has been deployed to: https://dsci-532-2025-28-commuting-insights.onrender.com/

### What has NOT been implemented?

- Line plot for `Average Commute Time` by `Time of Day`.
- Styling characteristics have not been developed.

### Changes to proposal

- The radio button for selecting the type of regional division has been removed. The app now focuses only on `Census Division`, excluding divisions by `Province` and `Census Sub-Divisions`. This change was made because `Census Sub-divisions` data was too large and lacked quality for proper display on the choropleth map.
- The individual dropdown widgets for selecting individual reference `census regions` have been replaced by a single dropdown for selecting the `census region` of interest.
- The bar chart displaying the proportion of commute counts by Commute Time Range has been removed, as its insights were redundant with the information already shown in the violin plots.
- The layout has been restructured into three sections: the sample selection section at the top, the choropleth map on the middle left, and descriptive visualizations on the bottom and right.

These changes minimize the impact on the app's intended purpose while reducing code complexity and visual clutter.

### Known Issues

- None identified.

### Deviations from Best Practices

- Outlier management in the data sample makes plots difficult to interpret, as the visualization areas are consumed by outliers.

### App Strengths, Limitations, Potential Future Improvements

- Strenghts: The app is responsive and aligned with expectations. It has a well-structured layout and follows best practices.
- Limitations: The dataset has multiple levels of categories for `Commuting Mode`, but only a few categories are currently displayed.
- Limitations: The app could be improved stylistically to enhance visual appeal.
- Limitations: The app's performance makes updates slow to display.
- Future Improvement: The scatter plot could display `Commuting Density` on the x-axis instead of `Total Census Records`, though this is difficult due to the lack of area data.
- Future Improvement: The app could be improved by recovering geographical categorization by `Province`.