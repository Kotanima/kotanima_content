from postgres import (
    connect_to_db,
    get_all_approved_posts,
    set_img_source_link_by_phash,
    set_invisible_tags_by_phash,
    set_mal_id_by_phash,
    set_visible_tags_by_phash,
)
from source_search import get_submission_source
from tags_resolver import get_mal_id_vis_and_invis_tags


def add_metadata_to_approved_posts():
    conn = connect_to_db()
    approved_posts = get_all_approved_posts(conn)

    for post in approved_posts:
        (
            mal_id,
            title,
            post_id,
            author,
            sub_name,
            phash,
            source_link,
            visible_tags,
        ) = post
        if not source_link and not visible_tags:
            src_link = get_submission_source(post_id, author)
            set_img_source_link_by_phash(conn, phash=phash, source_link=src_link)

        if not visible_tags:
            (
                res_anime_id,
                res_visible_tags,
                res_invis_tags,
            ) = get_mal_id_vis_and_invis_tags(conn, title)
            if res_visible_tags:
                set_visible_tags_by_phash(
                    conn, phash=phash, visible_tags=res_visible_tags
                )
            if res_invis_tags:
                set_invisible_tags_by_phash(
                    conn, phash=phash, invisible_tags=res_invis_tags
                )

            if not mal_id:
                set_mal_id_by_phash(conn, phash=phash, mal_id=res_anime_id)

    conn.close()


if __name__ == "__main__":
    add_metadata_to_approved_posts()
