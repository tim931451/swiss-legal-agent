"""T11: Fedlex ingestion. Parser on a small excerpt in the Akoma Ntoso format of Fedlex, plus the shipped data file."""

from lexgraph.rag.ingest import ARTICLES_FILE, anchor, load_articles, parse_fedlex

XML = """<?xml version="1.0" encoding="UTF-8"?>
<akomaNtoso xmlns="http://docs.oasis-open.org/legaldocml/ns/akn/3.0"><act><body>
<level eId="tit_8/lvl_O"><num>O. </num><heading>Beendigung des Mietverhältnisses</heading>
 <level eId="tit_8/lvl_O/lvl_3"><num>3. </num><heading>Wohnungen</heading>
  <article eId="art_266_c"><num><b>Art. 266</b><i>c</i><authorialNote><p>Fassung gemäss ...</p></authorialNote></num>
   <paragraph eId="art_266_c/para"><content><p>Bei der Miete von Wohnungen können die Parteien kündigen.</p></content>
   </paragraph></article>
  <article eId="art_274_274_g"><num><b>Art. 274-274g</b></num></article>
 </level></level>
<level eId="tit_10/lvl_G"><num>G. </num><heading>Kündigungsschutz</heading>
 <article eId="art_336_c"><num><b>Art. 336</b><i>c</i></num>
  <paragraph eId="art_336_c/para_1"><num>1</num><content><blockList>
   <listIntroduction>Der Arbeitgeber darf nicht kündigen:</listIntroduction>
   <item><num>a. </num><p>während des Militärdienstes;<authorialNote><p>Fussnote</p></authorialNote></p></item>
   <item><num>b. </num><p>während Krankheit.</p></item></blockList></content></paragraph>
  <paragraph eId="art_336_c/para_2"><num>2</num><content><p>Die Kündigung ist nichtig.</p></content></paragraph>
 </article>
 <article eId="art_343"><num><b>Art. 343</b></num><paragraph eId="art_343/para"><content><p>…</p></content>
 </paragraph></article>
</level>
<article eId="art_1"><num><b>Art. 1</b></num><paragraph><content><p>Outside both areas.</p></content></paragraph>
</article>
</body></act></akomaNtoso>""".encode()


def test_anchor_matches_fedlex():
    assert anchor("335c") == "art_335_c" and anchor("337") == "art_337"


def test_parse_fedlex_records():
    records = {r["id"]: r for r in parse_fedlex(XML, version="20261001")}
    assert set(records) == {"OR-266c", "OR-336c"}  # repealed 274-274g and 343 and Art. 1 are left out
    rent, work = records["OR-266c"], records["OR-336c"]
    assert rent["area"] == "mietrecht" and work["area"] == "arbeitsrecht"
    assert rent["title"] == "Wohnungen" and rent["context"] == "Beendigung des Mietverhältnisses › Wohnungen"
    assert rent["url"].endswith("#art_266_c") and rent["version"] == "2026-10-01"
    assert "Fassung" not in rent["text"] and "Fussnote" not in work["text"]
    assert work["text"] == ("1 Der Arbeitgeber darf nicht kündigen:\na. während des Militärdienstes;\n"
                            "b. während Krankheit.\n2 Die Kündigung ist nichtig.")


def test_data_file_is_real_fedlex_text():
    articles = load_articles(ARTICLES_FILE)
    ids = {a["id"] for a in articles}
    assert not any(a.get("placeholder") for a in articles)
    assert {"OR-253", "OR-273c", "OR-319", "OR-362", "OR-335c", "OR-336c", "OR-257d", "OR-259a"} <= ids
    assert {a["area"] for a in articles} == {"arbeitsrecht", "mietrecht"}


def test_testset_gold_articles_are_in_the_knowledge_base():
    """T09: every gold article must be retrievable, otherwise Hit@k and citation recall cannot reach 1."""
    ids = {a["id"] for a in load_articles(ARTICLES_FILE)}
    cases = load_articles(ARTICLES_FILE.parent / "testset.jsonl")
    assert len(cases) >= 10 and len({c["id"] for c in cases}) == len(cases)
    assert all(c["gold_articles"] and set(c["gold_articles"]) <= ids for c in cases)
