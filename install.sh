search_dir=/src/dist/*.tar.gz
for entry in $search_dir
do
  pip install "$entry"
done
