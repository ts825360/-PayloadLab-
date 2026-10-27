# SQLite selected source excerpt

This is a PayloadLab excerpt, not the full upstream Markdown snapshot.
Only the four CSV-selected metadata queries are retained.
Other sections are intentionally omitted after Windows Defender flagged the full reference.
Upstream: https://github.com/swisskyrepo/PayloadsAllTheThings/blob/3ac27901c711bdf3f5b65a7b1d1820a1f65bd09a/SQL%20Injection/SQLite%20Injection.md
Original full-file SHA-256: f6bad93117b22ac5575260d55967cb030f2780d8dcb70f5a9a5e16e82f1dbf36
Blank lines preserve the four upstream line anchors used by the unchanged CSV.
License: MIT; see ../LICENSE.
























```sql
select sqlite_version();
```





```sql
SELECT sql FROM sqlite_schema
SELECT sql FROM sqlite_master
SELECT tbl_name FROM sqlite_master WHERE type='table'
```
