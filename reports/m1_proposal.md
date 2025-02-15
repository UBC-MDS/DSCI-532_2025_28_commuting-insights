# COMMUTING INSIGHTS

Author Names:

Derek Rodgers  
Eugene You  
Han Wang  
Francisco Ramirez

## Motivation and purpose

The Canadian federal government is facing a critical challenge in addressing the growing concerns about transportation efficiency, environmental impact, and the quality of life for residents. One of the most pressing issues is the high dependency on cars for commuting, which not only leads to longer commute times but also contributes significantly to elevated CO2 emissions. This, in turn, exacerbates climate change, with widespread social, economic, and environmental consequences. As urbanization continues to spread across the country, understanding commuting patterns on a national scale has become essential for developing effective policies.

The purpose of this project is to assist the Canadian federal government by providing a comprehensive comparison of commuting patterns across all regions of Canada. This analysis will focus on the relationship between car dependency and commute times, aiming to identify trends that can inform national transportation policies. By examining the proportion of commutes made by car and the average commute times across the country, the project seeks to highlight regions where car dependency is particularly high, which may contribute to longer commute times and higher environmental impacts.

Through this comparison, the project will provide insights into how different regions across Canada are performing in terms of transportation efficiency and sustainability. This information will support the development of policies and infrastructure investments that aim to reduce car dependency, mitigate CO2 emissions, and improve overall commuting efficiency, benefiting residents nationwide.

## Description of the data

The dataset comes from [Statistics Canada](https://www.statcan.gc.ca/en/start) which is the national statistical office that offers access to key information on Canada's economy, society and environment. The selected dataset is called "Commuting duration by main mode of commuting and time arriving at work" and is located [here](https://www150.statcan.gc.ca/t1/tbl1/en/tv.action?pid=9810050301&geocode=A000011124). 

The dashboard will be visualizing a dataset of approximately 103,000 aggregated rows that contain commuting information in different census divisions and provices across Canada. Each example contains 12 associated variables
that describe the following charateristics, which we hypothesize could be helpful in comparing commuting status across regions in Canada:

- Geographical identifiers: `GEO`, `DGUID`, `Coordinate`
- Time of day range for commuting: `Time arriving at work`
- Mode of transportation: `Main mode of commuting`
- Count of records considered in aggregate: `Commuting duration:Total - Commuting duration`,
- Count of records by range of commuting time: `Commuting duration:Less than 15 minutes`, `Commuting duration:15 to 29 minutes`, `Commuting duration:30 to 44 minutes`, `Commuting duration:45 to 59 minutes`,  Commuting duration:60 minutes and over`
- Average commute duration: `Commuting duration:Average commuting duration (in minutes)`

No additional features are being considered to be engineered at the time of this report creation. However, additional information that is not part of the StatsCan dataset that would have proven useful in this dashboard include `total amount of minutes spent commuting by time range` to understand the origin of the featured `Commuting duration:Average commuting duration (in minutes)`, as well as `distance traversed during commute` to better understand the duration of the commutes.

The following table describes the data types of the columns planned to be used for the dashboard

| Data type               | Columns                                                      |
|-------------------------|--------------------------------------------------------------|
| Categorical - Nominal   | `GEO`, `DGUID`, `Coordinate`, `Main mode of commuting`       |
| Caterorical - Ordinal   | `Time arriving at work`                                      |
| Numeric - Integer       | All commuting durations                                      |
| Numeric - Float         | `Commuting duration:Average commuting duration (in minutes)` |

Note, the original data set contains six additional columns under the name `Symbol_` that will be be used for purposes of this project as they do not hold any relevant information. Additionally, a column named `REF_DATE` will not be used as it contains the year of the census data only, which is 2021 for all records.

## Research questions and usage scenarios

Persona description of a member of intended target audience: 

Joel is a policy maker, employee of [Transport Canada](https://tc.canada.ca/en) and he wants to gain insight as to how different means of transportation and different times of the day for commuting affect the duration of the population's commute. He particularly is interested in exploring how these habits compare between provinces and census divisions. He intends to use these insights to inform and frame his intervention policy in his own province and census division.

When Joel logs into the Commuting Insights application, he will be get an overview official census data, filter down to a sample of interest by region and means of transportation and use a geographical visualization of Canada that displays descriptive statistics in the form of a heatmap. He will also be able to access visualizations that describe variables of interest such as commuting time averages, proportion of commutes by means of transportation, and how commute times vary through different times of day. This will allow him to make head to head visual comparisons between different regions of interest.

Based on findings from using the Commuting Insights app, Joel will be able to perform follow up analysis to hypothesize how different means of transportation and commuting time of day affects the average commuting time for different regios across Canada. Based on this insight, Joel will be able to inform his policy intervention framework.

## App sketch & brief description

!["Dashboard"](../img/sketch.png)

The Commuting Insights dashboard is comprised of a main view that is divided into four main sections. 

The section on the left-hand side is focused on sample selection, where the data will be filtered to be segregated by Canadian province or by Census Division, and to be filtered by the commuting mode of interest (using a checkbox) and the time of day of the commute (using a slider). These filters will create the sample that will be present in the accompanying data visualizations. Additionally, two dropdown widgets will be available to select specific data points from the selected sample that could be used as reference and would be highlighted in the visualizations.

The top-middle section will be the main interface for the user to select a region of interest, where a map with subdivisions by province or census divisions will be displayed. Hovering/clicking on the map will define the region of interest that will be displayed as an additional data series in the visualizations. Hovering over the map will also display selected region information through a tooltip.

The bottom-middle section will display plots focused on the reference and the selected/hovered region points, comparing the proportion of commutes over and under 30 minutes, as well as comparing the average commute time for the reference and selected regions at different times of the day using a line plot.

Finally, on the right-hand side, plots including the entire selected sample will offer insight regarding where the reference and selected regions land in the context of the entire sample. These visualizationw will provide insight into how the amount of commutes in the region affect commute time, as well as how different commute times compare between commute modes.