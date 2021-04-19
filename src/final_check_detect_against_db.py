from tags_resolver import get_mal_id_vis_and_invis_tags
from postgres import connect_to_db


def get_all_scraped_titles(conn):
    with conn:
        with conn.cursor() as cursor:
            query = "SELECT title FROM my_app_redditpost WHERE sub_name IN ('awwnime', 'fantasymoe', 'awenime', 'patchuu', 'moescape')"
            cursor.execute(query)
            data = cursor.fetchall()
            return data


def main():
    # select all titles from scrape db
    # store logs about detected and undetected
    conn, _ = connect_to_db()
    titles = get_all_scraped_titles(conn)

    with open("FINAL.txt", 'w') as file:
        for title_tuple in titles:
            title = title_tuple[0]
            print(title)
            vis, invis = get_mal_id_vis_and_invis_tags(conn, title)
            file.write(title)
            file.write("\n")
            file.write("Visible:\n")
            file.write(vis)
            file.write("\n")
            file.write("Invisible:\n")
            file.write(invis)
            file.write("\n")
            file.write("\n")


if __name__ == "__main__":
    main()
