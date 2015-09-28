# Geotemporal input datasets

Datasets of hourly electricity prices and temperatures that can be used in
[Philharmonic](http://philharmonic.github.io/) to simulate energy consumption
of geographically-distributed clouds.

## Data description

The data is formated as comma-separated-values (CSV) for easy importing
into Pandas or Excel. The data is organised among the following files:

- prices.csv - real-time electricity prices ($/kWh)
- temperatures.csv - temperatures (C)
- locations.csv - the approximate coordinates of the cities

All the timestamps are shown in UTC.

The folder `usa` contains data for cities in the USA and represents real
historical values.

The folder `world` contains real data for US cities and real temperatures
for all the cities, but the electricity prices for non-US cities were
artificially generated as explained in [1].

## Using the data.

If you use the datasets in a publication, please cite [3] for the electricity
price data and [1] or [2] for the temperature data
([1] is newer and more detailed).

## References

```
[1] Dražen Lučanin, Ivona Brandić.
Pervasive Cloud Controller for Geotemporal Inputs.
IEEE Transactions on Cloud Computing (TCC), 2015.
```
([IEEE Xplore](http://ieeexplore.ieee.org/xpl/articleDetails.jsp?arnumber=7180314))

```
[2] Dražen Lučanin, Foued Jrad, Ivona Brandić, and Achim Streit.
Energy-Aware Cloud Management through Progressive SLA Specification.
Economics of Grids, Clouds, Systems, and Services - 11th International
Conference (GECON 2014). 16-18 September, 2014, Cardiff, UK.
```
([arXiv](http://arxiv.org/abs/1409.0325),
[SpringerLink](http://link.springer.com/chapter/10.1007/978-3-319-14609-6_6))

```
[3] Alfeld, S., Barford, C., Barford, P.: Toward an analytic framework
for the electrical power grid. In: Proceedings of the 3rd International
Conference on Future Energy Systems: Where Energy, Computing and
Communication Meet. pp. 9:1-9:4. e-Energy '12, ACM, New York, NY, USA (2012).
```
([ACM DL](http://dl.acm.org/citation.cfm?id=2208837))
