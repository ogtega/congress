# polist_congress

## Database model for congress
### Member
```
{
	_id: <*string>, // Bioguide ID
	first_name: <string>,
	last_name: <string>,
	party: <string>,
}
```
### Term
```
{
	congress: <*int>,
	member_id: <*MemberID>,
	chamber: *enum['house', 'senate'],
	state: <*StateID>,
	district: <*DistrictID?>,
	class: <int?>
}
```
### District
```
{
	_id: <*string>,
	state: <*StateID>
	geojson: <*GeoJSON>,
}
```
### State
```
{
	_id: <*string>,
	fips: <*string>,
    name: <*string>
}
```
