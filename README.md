Path: 
http://hymnalnetapi.herokuapp.com

Route:
/search
Parameters:
search_parameter
page_num (Optional)

Route:
/hymn
Parameters:
hymn_type
hymn_number
check_exists (will return the hymn if it exists on hymnal.net and throw 400 if it doesn't)

Route:
/list
Parameters:
song_type
letter (Required only if song_type is not "scripture")
testament (Required only if song_type is "scripture")
