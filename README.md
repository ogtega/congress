# polist_congress

## Database model for congress
### Member
```
{
	_id: <string>, // Bioguide ID
	first_name: <string>,
	last_name: <string>,
	party: <string>,
	last_term: <Term>
}
```
### Committee
```
{
	_id: <string>, // Committee code
	name: <string>
}
```
### Term
```
{
	congress: <int>,
	member: <Member>,
	chamber: enum['house', 'senate'],
	state: <State>,
	district: <District?>,
	class: <int?>,
	committees: <Committee>[]
}
```
### Bill
```
{
	title: <string>,
	congress: <int>,
	subjects: <string>[],
	summary: <string>,
	sponsors: <string>[],
	cosponsors: <string>[],
	votes: <Vote>[]
}
```
### Vote
```
{
	member: <Member>,
	bill: <Bill>,
	vote: enum['y', 'n', 'a']
}
```
### District
```
{
	_id: <string>,
	state: <State>
	geojson: <GeoJSON>,
	rep: <Member> // // Used to keep track of if a term needs to be updated
}
```
### State
```
{
	_id: <string>,
	fips: <string>,
	name: <string>,
	reps: <Member>[] // Used to keep track of if a term needs to be updated
}
```
