from chatol.html import extract_csrf_token, extract_projects_payloads, looks_like_login_page


def test_extract_csrf_token_from_meta():
    html = '<html><head><meta name="ol-csrfToken" content="csrf-123"></head></html>'

    assert extract_csrf_token(html) == "csrf-123"


def test_extract_projects_payloads_from_prefetched_meta():
    html = """
    <html><head>
      <meta name="ol-prefetchedProjectsBlob" content='{&quot;projects&quot;:[{&quot;id&quot;:&quot;p1&quot;,&quot;name&quot;:&quot;Paper&quot;}]}' />
    </head></html>
    """

    payloads = extract_projects_payloads(html)

    assert payloads == [{"projects": [{"id": "p1", "name": "Paper"}]}]


def test_extract_projects_payloads_from_mixed_case_raw_list_meta():
    html = """
    <html><head>
      <meta name="ol-prefetchedProjectsBlob" content='[{&quot;id&quot;:&quot;p2&quot;,&quot;name&quot;:&quot;Raw List&quot;}]' />
    </head></html>
    """

    payloads = extract_projects_payloads(html)

    assert payloads == [[{"id": "p2", "name": "Raw List"}]]


def test_looks_like_login_page():
    assert looks_like_login_page('<form name="loginForm"><input name="password"></form>')
    assert not looks_like_login_page('<main>Project list</main>')
