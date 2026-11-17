"""Live issuer scope checks, not owner article approval."""
import unittest
from v166_e4_attributed_book_snapshot import body_scope,load_registry,PDF_PAGES
from v166_e4_bibliographic_primary import fetch_wiley_publisher_bytes
from v166_e4_wiley_author_chapter import fetch_wiley_original_chapter_pdf

class LiveBookScopeTests(unittest.TestCase):
    def test_all_registered_scope_keys_replayed_at_live_issuer(self):
        rows=load_registry()["rows"]
        html=fetch_wiley_publisher_bytes()
        pdf=fetch_wiley_original_chapter_pdf()
        for cid,(_,_,key) in rows.items():
            with self.subTest(claim_id=cid,scope=key):
                proof=body_scope(pdf if key in PDF_PAGES else html,key,archive=False)
                self.assertIn(proof["format"],{"chapter","html"})

if __name__=="__main__":
    unittest.main()
