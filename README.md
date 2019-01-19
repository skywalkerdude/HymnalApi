http://hymnalnetapi.herokuapp.com

Route:<br/>
/search<br/>
Parameters:<br/>
search_parameter<br/>
page_num (Optional)


Route:<br/>
/hymn<br/>
Parameters:<br/>
hymn_type<br/>
hymn_number<br/>
check_exists (will return the hymn if it exists on hymnal.net and throw 400 if it doesn't)


Route:<br/>
/list<br/>
Parameters:<br/>
song_type<br/>
letter (Required only if song_type is not "scripture")<br/>
testament (Required only if song_type is "scripture")
