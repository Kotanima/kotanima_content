"""
Use detection modules and store the results in the database
"""
try:
    from postgres import (
        connect_to_db,
        get_posts_for_metadata,
        set_img_source_link_by_phash,
        set_invisible_tags_by_phash,
        set_mal_id_by_phash,
        set_visible_tags_by_phash,
    )
    from source_search import get_submission_source
    from tags_resolver import get_mal_id_vis_and_invis_tags
    from models import IdentifiedRedditPost
except ModuleNotFoundError:
    from src.postgres import (
        connect_to_db,
        get_posts_for_metadata,
        set_img_source_link_by_phash,
        set_invisible_tags_by_phash,
        set_mal_id_by_phash,
        set_visible_tags_by_phash,
    )
    from src.source_search import get_submission_source
    from src.tags_resolver import get_mal_id_vis_and_invis_tags
    from src.models import IdentifiedRedditPost


def add_metadata_to_approved_posts() -> None:
    conn = connect_to_db()
    approved_posts = get_posts_for_metadata(conn)

    for count, post in enumerate(approved_posts):
        r_post = IdentifiedRedditPost.from_metadata_db(post)

        print(f"Adding metadata to {count}/{len(approved_posts)-1}")
        if count == 5113:
            print(r_post)

        if not r_post.source_link and not r_post.visible_tags:
            src_link = get_submission_source(r_post.post_id, r_post.author)
            set_img_source_link_by_phash(conn, phash=r_post.phash, source_link=src_link)

        if not r_post.visible_tags:
            (
                res_anime_id,
                res_visible_tags,
                res_invis_tags,
            ) = get_mal_id_vis_and_invis_tags(conn, r_post.title)
            if res_visible_tags:
                set_visible_tags_by_phash(
                    conn, phash=r_post.phash, visible_tags=res_visible_tags
                )
            if res_invis_tags:
                set_invisible_tags_by_phash(
                    conn, phash=r_post.phash, invisible_tags=res_invis_tags
                )

            if not r_post.mal_id and res_anime_id: 
                set_mal_id_by_phash(conn, phash=r_post.phash, mal_id=res_anime_id)

    conn.close()


if __name__ == "__main__":
    add_metadata_to_approved_posts()
