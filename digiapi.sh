curl -G \
  --data-urlencode "action=registerUser" \
  --data-urlencode "user=user" \
  --data-urlencode "pass=md5hash" \
  https://digiapis.rcs-rds.ro/digionline/api/v13/user.php