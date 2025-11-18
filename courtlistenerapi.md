Api Root
The default basic root view for DefaultRouter

GET /api/rest/v4/
HTTP 200 OK
Allow: GET, HEAD, OPTIONS
Content-Type: application/json
Vary: Accept

{
    "search": "https://www.courtlistener.com/api/rest/v4/search/",
    "dockets": "https://www.courtlistener.com/api/rest/v4/dockets/",
    "originating-court-information": "https://www.courtlistener.com/api/rest/v4/originating-court-information/",
    "docket-entries": "https://www.courtlistener.com/api/rest/v4/docket-entries/",
    "recap-documents": "https://www.courtlistener.com/api/rest/v4/recap-documents/",
    "courts": "https://www.courtlistener.com/api/rest/v4/courts/",
    "audio": "https://www.courtlistener.com/api/rest/v4/audio/",
    "clusters": "https://www.courtlistener.com/api/rest/v4/clusters/",
    "opinions": "https://www.courtlistener.com/api/rest/v4/opinions/",
    "opinions-cited": "https://www.courtlistener.com/api/rest/v4/opinions-cited/",
    "tag": "https://www.courtlistener.com/api/rest/v4/tag/",
    "people": "https://www.courtlistener.com/api/rest/v4/people/",
    "disclosure-typeahead": "https://www.courtlistener.com/api/rest/v4/disclosure-typeahead/",
    "positions": "https://www.courtlistener.com/api/rest/v4/positions/",
    "retention-events": "https://www.courtlistener.com/api/rest/v4/retention-events/",
    "educations": "https://www.courtlistener.com/api/rest/v4/educations/",
    "schools": "https://www.courtlistener.com/api/rest/v4/schools/",
    "political-affiliations": "https://www.courtlistener.com/api/rest/v4/political-affiliations/",
    "sources": "https://www.courtlistener.com/api/rest/v4/sources/",
    "aba-ratings": "https://www.courtlistener.com/api/rest/v4/aba-ratings/",
    "parties": "https://www.courtlistener.com/api/rest/v4/parties/",
    "attorneys": "https://www.courtlistener.com/api/rest/v4/attorneys/",
    "recap": "https://www.courtlistener.com/api/rest/v4/recap/",
    "recap-email": "https://www.courtlistener.com/api/rest/v4/recap-email/",
    "recap-fetch": "https://www.courtlistener.com/api/rest/v4/recap-fetch/",
    "recap-query": "https://www.courtlistener.com/api/rest/v4/recap-query/",
    "fjc-integrated-database": "https://www.courtlistener.com/api/rest/v4/fjc-integrated-database/",
    "tags": "https://www.courtlistener.com/api/rest/v4/tags/",
    "docket-tags": "https://www.courtlistener.com/api/rest/v4/docket-tags/",
    "prayers": "https://www.courtlistener.com/api/rest/v4/prayers/",
    "increment-event": "https://www.courtlistener.com/api/rest/v4/increment-event/",
    "visualizations/json": "https://www.courtlistener.com/api/rest/v4/visualizations/json/",
    "visualizations": "https://www.courtlistener.com/api/rest/v4/visualizations/",
    "agreements": "https://www.courtlistener.com/api/rest/v4/agreements/",
    "debts": "https://www.courtlistener.com/api/rest/v4/debts/",
    "financial-disclosures": "https://www.courtlistener.com/api/rest/v4/financial-disclosures/",
    "gifts": "https://www.courtlistener.com/api/rest/v4/gifts/",
    "investments": "https://www.courtlistener.com/api/rest/v4/investments/",
    "non-investment-incomes": "https://www.courtlistener.com/api/rest/v4/non-investment-incomes/",
    "disclosure-positions": "https://www.courtlistener.com/api/rest/v4/disclosure-positions/",
    "reimbursements": "https://www.courtlistener.com/api/rest/v4/reimbursements/",
    "spouse-incomes": "https://www.courtlistener.com/api/rest/v4/spouse-incomes/",
    "alerts": "https://www.courtlistener.com/api/rest/v4/alerts/",
    "docket-alerts": "https://www.courtlistener.com/api/rest/v4/docket-alerts/",
    "memberships": "https://www.courtlistener.com/api/rest/v4/memberships/",
    "citation-lookup": "https://www.courtlistener.com/api/rest/v4/citation-lookup/"
}

Legal Citation API
Use these APIs to analyze and query the network of citations between legal cases.

These APIs are powered by Eyecite, our tool for identifying citations in legal text. Using that tool, we have identified millions of citations between legal decisions, which you can query using these APIs.

These citations power our visualizations, tables of authorities, citation search, and more.

To look up specific citations, see our citation lookup and verification API.

Opinions Cited/Citing API
/api/rest/v4/opinions-cited/
This endpoint provides an interface into the citation graph that CourtListener provides between opinions in our case law database.

You can look up the field descriptions, filtering, ordering, and rendering options by making an OPTIONS request:

curl -v \
  -X OPTIONS \
  --header 'Authorization: Token <your-token-here>' \
  "https://www.courtlistener.com/api/rest/v4/opinions-cited/"
That query will return the following filter options:

{
  "id": {
    "type": "NumberRangeFilter",
    "lookup_types": [
      "exact",
      "gte",
      "gt",
      "lte",
      "lt",
      "range"
    ]
  },
  "citing_opinion": {
    "type": "RelatedFilter",
    "lookup_types": "See available filters for 'Opinions'"
  },
  "cited_opinion": {
    "type": "RelatedFilter",
    "lookup_types": "See available filters for 'Opinions'"
  }
}
To understand RelatedFilters, see our filtering documentation.

These filters allow you to filter to the opinions that an opinion cites (its "Authorities" or backward citations) or the later opinions that cite it (forward citations).

For example, opinion 2812209 is the decision in Obergefell v. Hodges. To see what it cites:

curl -v \
  --header 'Authorization: Token <your-token-here>' \
  "https://www.courtlistener.com/api/rest/v4/opinions-cited/?citing_opinion=2812209"
Which returns (in part):

{
  "count": 75,
  "next": "https://www.courtlistener.com/api/rest/v4/opinions-cited/?citing_opinion=2812209&cursor=cD0xMjA5NjAyMg%3D%3D",
  "previous": null,
  "results": [
    {
      "resource_uri": "https://www.courtlistener.com/api/rest/v4/opinions-cited/167909003/",
      "id": 167909003,
      "citing_opinion": "https://www.courtlistener.com/api/rest/v4/opinions/2812209/",
      "cited_opinion": "https://www.courtlistener.com/api/rest/v4/opinions/96405/",
      "depth": 1
    },
    {
      "resource_uri": "https://www.courtlistener.com/api/rest/v4/opinions-cited/167909002/",
      "id": 167909002,
      "citing_opinion": "https://www.courtlistener.com/api/rest/v4/opinions/2812209/",
      "cited_opinion": "https://www.courtlistener.com/api/rest/v4/opinions/2264443/",
      "depth": 1
    },
…
To go the other direction, and see what cites Obergefell, use the cited_opinion parameter instead:

curl -v \
  --header 'Authorization: Token <your-token-here>' \
  "https://www.courtlistener.com/api/rest/v4/opinions-cited/?cited_opinion=2812209"
That returns (in part):

{
  "count": 403,
  "next": "https://www.courtlistener.com/api/rest/v4/opinions-cited/?cited_opinion=2812209&page=2",
  "previous": null,
  "results": [
    {
      "resource_uri": "https://www.courtlistener.com/api/rest/v4/opinions-cited/213931728/",
      "id": 213931728,
      "citing_opinion": "https://www.courtlistener.com/api/rest/v4/opinions/10008139/",
      "cited_opinion": "https://www.courtlistener.com/api/rest/v4/opinions/2812209/",
      "depth": 4
    },
…
Note that:

The depth field indicates how many times the cited opinion is referenced by the citing opinion. In the example above opinion 10008139 references Obergefell (2812209) four times. This may indicate that Obergefell is an important authority for 10008139.

Opinions are often published in more than one book or online resource. Therefore, many opinions have more than one citation to them. These are called "parallel citations." We do not have every parallel citation for every decision. This can impact the accuracy of the graph.

Frequently, we backfill citations, adding a new citation to an older case. When we do this, we do not always re-run our citation linking utility. This means that any later cases that referred to the newly-added citation may not be linked to it for some time.

Citation Lookup and Verification API
/api/rest/v4/citation-lookup/
Use this API to look up citations in CourtListener's database of 18,070,263 citations.

This API can look up either an individual citation or can parse and look up every citation in a block of text. This can be useful as a guardrail to help prevent hallucinated citations.

This API uses Eyecite, a tool we developed with Harvard Library Innovation Lab to parse legal citations. To develop Eyecite, we analyzed more than 50 million citations going back more than two centuries. We believe we have identified every reporter abbreviation in American case law and that there is no case law citation that Eyecite cannot properly parse and interpret.

This API uses the same authentication and serialization methods as the rest of the CourtListener APIs. It does not support filtering, pagination, ordering, or field selection.

Usage
The simplest way to query this API is to send it a blob of text. If the text does not have any citations, it will simply return an empty JSON object:

curl -X POST "https://www.courtlistener.com/api/rest/v4/citation-lookup/" \
  --header 'Authorization: Token <your-token-here>' \
  --data 'text=Put some text here'\
[]
If the text contains valid citations, it will return a list of the citations, analyzing each. This example contains a single citation that is found:

curl -X POST "https://www.courtlistener.com/api/rest/v4/citation-lookup/" \
  --header 'Authorization: Token <your-token-here>' \
  --data 'text=Obergefell v. Hodges (576 U.S. 644) established the right to marriage among same-sex couples'
[
  {
    "citation": "576 U.S. 644",
    "normalized_citations": [
      "576 U.S. 644"
    ],
    "start_index": 22,
    "end_index": 34,
    "status": 200,
    "error_message": "",
    "clusters": [...one large cluster object here...]
  }
]
If you have the volume, reporter, and page for a citation, you can look it up as follows:

curl -X POST "https://www.courtlistener.com/api/rest/v4/citation-lookup/" \
  --header 'Authorization: Token <your-token-here>' \
  --data 'volume=576' \
  --data 'reporter=U.S.' \
  --data 'page=644'
That returns the same response as above.

Field Definitions
The fields returned by this API are:

citation — The citation you looked up. If you supplied the volume, reporter, and page, they will appear here as a single space-separated string.

normalized_citations — Normalized versions of your citation if it contains a typo or if it is not the canonical (standard) abbreviation for a reporter. If the citation queried is ambiguous, more than one item can appear in this field. See examples below.

start_index & end_index — These fields indicate the start and end positions where a citation is found in the text queried.

status — indicates the outcome of a citation lookup. Its values correspond to HTTP status codes and can have one of five values:

200 (OK) — We found a citation, it was valid, and we were able to look it up in CourtListener.

404 (Not Found) — We found a citation, it was valid, but we were unable to look it up in CourtListener.

400 (Bad Request) — We found something that looks like a citation, but the reporter in the citation wasn’t in our system (e.g., “33 Umbrella 422” looks like a citation, but is not valid).

300 (Multiple Choices) — We found a valid citation, it was valid, but it matched more than one item in CourtListener.

429 (Too Many Requests) — This API will only lookup 250 citations in a single request. Any citations after that point will have this status. They will be identified but will not be looked up. (See throttles below)

error_message — This field will contain additional details about any problems the lookup encounters.

clusters — This is a list of the CourtListener cluster objects that match the citation in your query. This key will contain multiple values when a citation matches more than one legal decision. This can happen when a citation is ambiguous or when multiple decisions are on a single page in a printed book (and thus share the same citation).

Limitations & Throttles
This API has four limitations on how much it can be used:

The performance of this API is affected by the number of citations it has to look up. Therefore, it is throttled to 60 valid citations per minute. If you are below this throttle, you will be able to send a request to the API. If a request pushes you beyond this throttle, further requests will be denied. When your request is denied, the API will respond with a 429 HTTP code and a JSON object. The JSON object will contain a wait_util key that uses an ISO-8601 datetime to indicate when you will be able to make your next request.

The API will look up at most 250 citations in any single request. Any citations past that point will be parsed, but not matched to the CourtListener database. The status key of such citations will be 429, indicating “Too many citations requested.” See examples below for details.

Text lookup requests to this API can only contain 64,000 characters at a time. Requests with more than this amount will be blocked for security. This is about 50 pages of legal content.

To prevent denial of service attacks that do not contain any citations, this API has the same request throttle rates as the other CourtListener APIs. This way, even requests that do not contain citations can be throttled. (Most users will never encounter this throttle.)

A few other limitations to be aware of include:

This API does not look up statutes, law journals, id, or supra citations. If you wish to match such citations, please use Eyecite directly.

This API will not attempt to match citations without volume numbers or page numbers (e.g. 22 U.S. ___).

API Examples
Basic, Valid Lookup
The following is a basic lookup using the text parameter and a block of text:

curl -X POST "https://www.courtlistener.com/api/rest/v4/citation-lookup/" \
  --header 'Authorization: Token <your-token-here>' \
  --data 'text=Obergefell v. Hodges (576 U.S. 644) established the right to marriage among same-sex couples'
[
  {
    "citation": "576 U.S. 644",
    "normalized_citations": [
      "576 U.S. 644"
    ],
    "start_index": 22,
    "end_index": 34,
    "status": 200,
    "error_message": "",
    "clusters": [...one cluster here...]
  }
]
Failed Lookup
This query uses the volume-reporter-page triad, but fails because the citation does not exist:

curl -X POST "https://www.courtlistener.com/api/rest/v4/citation-lookup/" \
  --header 'Authorization: Token <your-token-here>' \
  --data 'volume=1' \
  --data 'reporter=U.S.' \
  --data 'page=200'
[
  {
    "citation": "1 U.S. 200",
    "normalized_citations": [
      "1 U.S. 200"
    ],
    "start_index": 0,
    "end_index": 10,
    "status": 404,
    "error_message": "Citation not found: '1 U.S. 200'",
    "clusters": []
  }
]
Note that:

The status field is set to 404 indicating the citation was not found.

The start_index is 0, and the end_index is the length of the citation including space separators.

The error_message field provides details of the error.

Throttled Citations
If your request contains more than 250 citations, the 251st and subsequent citations will be returned with 429 status fields:

curl -X POST "https://www.courtlistener.com/api/rest/v4/citation-lookup/" \
  --header 'Authorization: Token <your-token-here>' \
  --data 'text=Imagine a very long blob here, with 251 citations.'
[
  ...250 citations would appear here, then the 251st and subsequent citations would be...
  {
    "citation": "576 U.S. 644",
    "normalized_citations": [
      "576 U.S. 644"
    ],
    "start_index": 10002,
    "end_index": 10013,
    "status": 429,
    "error_message": "Too many citations requested.",
    "clusters": []
  }
]
Note that:

All citations will be parsed and will provide normalized versions and index locations.

Citations after the 250th will return a status of 429, indicating "Too many citations requested."

A follow-up query that begins on the 251st start_index (in this case number 10002) will look up the next 250 items.

Typoed/Non-Canonical Reporter Abbreviation
If you query the non-canonical reporter abbreviation or if your reporter contains a known typo, we will provide the corrected citation in the normalized_citations key. The following example looks up a citation using "US" instead of the correct "U.S.":

curl -X POST "https://www.courtlistener.com/api/rest/v4/citation-lookup/" \
  --header 'Authorization: Token <your-token-here>' \
  --data 'text=576 US 644'
[
  {
    "citation": "576 US 644",
    "normalized_citations": [
      "576 U.S. 644"
    ],
    "start_index": 1,
    "end_index": 11,
    "status": 200,
    "error_message": "",
    "clusters": [...one cluster here...]
  }
]
Ambiguous Citation
This lookup is for an ambiguous citation abbreviated as "H." This reporter abbreviation can refer to Handy's Ohio Reports, the Hawaii Reports, or Hill’s New York Reports. Only two of those reporter series have cases at the queried volume and page number, so the API returns two possible matches for the citation:

curl -X POST "https://www.courtlistener.com/api/rest/v4/citation-lookup/" \
  --header 'Authorization: Token <your-token-here>' \
  --data 'text=1 H. 150'
[
  {
    "citation": "1 H. 150",
    "normalized_citations": [
      "1 Handy 150",
      "1 Haw. 150",
      "1 Hill 150"
    ],
    "start_index": 0,
    "end_index": 8,
    "status": 300,
    "clusters": [
      {
        ...
        "citations": [{
          "volume": 1,
          "reporter": "Handy",
          "page": "150",
          "type": 2
        }],
       ...
       "case_name": "Louis v. Steamboat Buckeye",
       ...
      },
      {
        ...
        "citations": [{
          "volume": 1,
          "reporter": "Haw.",
          "page": "150",
          "type": 2
        }],
        ...
        "case_name": "Fell v. Parke",
        ...
      }
    ]
  }
]
Note that:

The normalized_citations field returned three possible values for the ambiguous query.

The status field returned a 300 code, indicating "Multiple Choices."

There are two different objects returned in the clusters field.


REST API – v4.3
APIs for developers and researchers that need granular legal data.

After more than a decade of development, these APIs are powerful. Our case law API was the first. Our PACER and oral argument APIs are the biggest. Our webhooks push data to you. Our citation lookup tool can fight hallucinations in AI tools.

Let's get started. To see and browse all the API URLs, click the button below:


We could have also pulled up that same information using curl, with a command like:

curl "https://www.courtlistener.com/api/rest/v4/"
Note that when you press the button in your browser, you get an HTML result, but when you run curl you get a JSON object. This is discussed in more depth below.

 Listen Up! Something else that's curious just happened. You didn't authenticate to the API. To encourage experimentation, many of our APIs are open by default. The biggest gotcha people have is that they forget to enable authentication before deploying their code. Don't make this mistake! Remember to add authentication.

The APIs listed in this response can be used to make queries against our database or search engine.

To learn more about an API, you can send an HTTP OPTIONS request, like so:

curl -X OPTIONS "https://www.courtlistener.com/api/rest/v4/"
An OPTIONS request is one of the best ways to understand the API.

Support
Questions about the APIs can be sent to our GitHub Discussions forum or via our contact form.

We prefer that questions be posted in the forum so they can help others. If you are a private organization posting to that forum, we will avoid sharing details about your organization.

 

Data Models
The two images below show how the APIs work together. The first image shows the models we use for people, and the second shows the models we use for documents and metadata about them. You can see that these models currently link together on the Docket, Person, and Court tables. (Here's a version of this diagram that shows everything all at once.)





API Overview
This section explains the general principles of the API. These principals are driven by the features supported by the Django REST Framework. To go deep on any of these sections, we encourage you to check out the documentation there.

Permissions
Some of our APIs are only available to select users. If you need greater access to these APIs, please get in touch.

All other endpoints are available according to the throttling and authentication limitations listed below.

Your Authorization Token

Authentication
Authentication is necessary to monitor and throttle the system, and so we can assist with any errors that may occur.

Per our privacy policy, we do not track your queries in the API, though we do collect statistical information for system monitoring.

There are currently three types of authentication available on the API:

HTTP Token Authentication
Cookie/Session Authentication
HTTP Basic Authentication
All of these methods are secure, so the choice of which to use is generally a question of what's most convenient for the context of your work. Our recommendations are:

Use Token Authentication for programmatic API access.
Use Cookie/Session Authentication if you already have a user's cookie or are developing a system where you can ask the user to log into CourtListener.
Use Basic Authentication if that's all your client supports.
Token Authentication
To use token authentication, use the Authorization HTTP Header. The key should prefix the Token, with whitespace separating the two strings. For example:

Authorization: Token <your-token-here>
Using curl, this looks like:

curl "https://www.courtlistener.com/api/rest/v4/clusters/" \
  --header 'Authorization: Token <your-token-here>'
Note that quotes are used to enclose the whitespace in the header.

 Careful! A common mistake is to forget the word "Token" in the header.

Sign in to see your authorization token in this documentation.

Cookie Authentication
To use Cookie Authentication log into Courtlistener and pass the cookie value using the standard cookie headers.

HTTP Basic Authentication
To do HTTP Basic Authentication using curl, you might do something like this:

curl --user "harvey:your-password" \
  "https://www.courtlistener.com/api/rest/v4/clusters/"
You can also do it in your browser with a url like:

https://harvey:your-password@www.courtlistener.com/api/rest/v4/clusters/
But if you're using your browser, you might as well just log in.

Serialization Formats
Requests may be serialized as HTML, JSON, or XML. JSON is the default if no format is specified. The format you wish to receive is requested via the HTTP Accept header.

The following media types and parameters can be used:

HTML: The media type for HTML is text/html.
JSON: The media type for JSON is application/json. Providing the indent media type parameter allows clients to set the indenting for the response, for example: Accept: application/json; indent=2.
XML: The media type for XML is application/xml.
By default, browsers send an Accept header similar to:

text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8
This states that text/html is the preferred serialization format. The API respects that, returning HTML when requested by a browser and returning JSON when no Accept header is provided, because JSON is the default.

If you wish to set the Accept header using a tool like cURL, you can do so using the --header flag:

curl --header "Accept: application/xml" \
  "https://www.courtlistener.com/api/rest/v4/clusters/"
All data is serialized using the utf-8 charset.

Parsing Uploaded Content
If you are a user that has write access to these APIs (most users do not), you will need to use the Content-Type HTTP header to explicitly set the format of the content you are uploading. The header can be set to any of the values that are available for serialization or to application/x-www-form-urlencoded or multipart/form-data, if you are sending form data.

Filtering
With the exception of the search API, these APIs can be filtered using a technique similar to Django's field lookups.

To see how an endpoint can be filtered, do an OPTIONS request on the API and inspect the filters key in the response.

In the filters key, you'll find a dictionary listing the fields that can be used for filtering along with their types, lookup fields, and any values (aka choices) that can be used for specific lookups.

For example, this uses jq to look at the filters on the docket API:

curl -X OPTIONS \
  --header 'Authorization: Token <your-token-here>' \
  "https://www.courtlistener.com/api/rest/v4/dockets/" | jq '.filters'
That returns something like:

{
  "id": {
    "type": "NumberRangeFilter",
    "lookup_types": [
      "exact",
      "gte",
      "gt",
      "lte",
      "lt",
      "range"
    ]
  },
...
This means that you can filter dockets using the ID field, and that you can do exact, greater than or equal, greater than, less than or equal, less than, or range filtering.

You can use these filters with a double underscore. For example, this gets IDs greater than 500 and less than 1,000:

curl \
  --header 'Authorization: Token <your-token-here>' \
  "https://www.courtlistener.com/api/rest/v4/dockets/?id__gt=500&id__lt=1000" | jq '.count'
499
It also allows ranges (inclusive):

curl \
  --header 'Authorization: Token <your-token-here>' \
  "https://www.courtlistener.com/api/rest/v4/dockets/?id__range=500,1000" | jq '.count'
501
Filters can be combined using multiple GET parameters.

There are a few special types of filters. The first are Related Filters, which allow you to join filters across APIs. For example, when you are using the docket API, you'll see that it has a filter for the court API:

"court": {
    "type": "RelatedFilter",
    "lookup_types": "See available filters for 'Courts'"
}
This means that you can use any of the court filters on the docket API. If you do an OPTIONS request on the court API, you'll see its filters:

curl -X OPTIONS \
  --header 'Authorization: Token <your-token-here>' \
  "https://www.courtlistener.com/api/rest/v4/courts/" | jq '.filters'
Again, one of the filters is the ID field, but it only allows exact values on this API:

"id": {
    "type": "CharFilter",
    "lookup_types": [
        "exact"
    ]
}
Putting this together, here's how you look up dockets for a particular court:

curl \
  --header 'Authorization: Token <your-token-here>' \
  "https://www.courtlistener.com/api/rest/v4/dockets/?court=scotus&id__range=500,1000" | jq '.count'
36
This opens up many possibilities. For example, another filter on the Court endpoint is for jurisdictions. To use it, you would use a GET parameter like court__jurisdictions=FD. In this case, the double underscore allows you to join the filter from the other court API to the docket API.

If you want to join a filter, you could do something like court__full_name__startswith=district. That would return dockets in courts where the court's name starts with "district".

RelatedFilters can span many objects. For example, if you want to get all the Supreme Court Opinion objects, you will need to do that with a query such as:

curl "https://www.courtlistener.com/api/rest/v4/opinions/?cluster__docket__court=scotus"
This uses the Opinion API to get Opinions that are part of Opinion Clusters that are on Dockets in the Court with the ID of scotus. To understand this data model better, see the case law API documentation.

To use date filters, supply dates in ISO-8601 format.

A final trick that can be used with the filters is the exclusion parameter. Any filter can be converted into an exclusion filter by prepending it with an exclamation mark. For example, this returns Dockets from non-Federal Appellate jurisdictions:

curl "https://www.courtlistener.com/api/rest/v4/dockets/?court__jurisdiction!=F"
You can see more examples of filters in our automated tests.

Ordering
With the exception of the search API, you can see which fields can be used for ordering, by looking at the ordering key in an OPTIONS request. For example, the Position endpoint contains this:

"ordering": [
    "id",
    "date_created",
    "date_modified",
    "date_nominated",
    "date_elected",
    "date_recess_appointment",
    "date_referred_to_judicial_committee",
    "date_judicial_committee_action",
    "date_hearing",
    "date_confirmation",
    "date_start",
    "date_retirement",
    "date_termination"
]
Thus, you can order using any of these fields in conjunction with the order_by parameter.

Descending order can be done using a minus sign. Multiple fields can be requested using a comma-separated list. This, for example, returns judicial Positions ordered by the most recently modified, then by the most recently elected:

curl "https://www.courtlistener.com/api/rest/v4/positions/?order_by=-date_modified,-date_elected"
Ordering by fields with duplicate values is non-deterministic. If you wish to order by such a field, you should provide a second field as a tie-breaker to consistently order results. For example, ordering by date_filed will not return consistent ordering for items that have the same date, but this can be fixed by ordering by date_filed,id. In that case, if two items have the same date_filed value, the tie will be broken by the id field.

Counting
To retrieve the total number of items matching your query without fetching all the data, you can use the count=on parameter. This is useful for verifying filters and understanding the scope of your query results without incurring the overhead of retrieving full datasets.

curl "https://www.courtlistener.com/api/rest/v4/opinions/?cited_opinion=32239&count=on"

{"count": 3302}
When count=on is specified:

The API returns only the count key with the total number of matching items.
Pagination parameters like cursor are ignored.
The response does not include any result data, which can improve performance for large datasets.
In standard paginated responses, a count key is included with the URL to obtain the total count for your query:

curl "https://www.courtlistener.com/api/rest/v4/opinions/?cited_opinion=32239"

{
  "count": "https://www.courtlistener.com/api/rest/v4/opinions/?cited_opinion=32239&count=on",
  "next": "https://www.courtlistener.com/api/rest/v4/opinions/?cited_opinion=32239&cursor=2",
  "previous": null,
  "results": [
    // paginated results
  ]
}
You can follow this URL to get the total count of items matching your query.

Field Selection
To save bandwidth, increase serialization performance, and optimize our backend queries, fields can be limited by using the fields parameter to select only the fields you want and the omit parameter to omit fields you do not. Each parameter accepts a comma-separated list of fields. Double-underscore __ notation is used to choose or omit nested fields.

This is an important optimization, particularly for resources with large fields.

For example, to only receive the educations and date_modified fields from the Judge endpoint you could do:

curl "https://www.courtlistener.com/api/rest/v4/people/?fields=educations,date_modified"
{
  "educations": [
    ...nested values here...
  ],
  "date_modified": "2023-03-31T07:15:28.409594-07:00"
},
...
Or, to include only the date_modified and id fields within each education entry (note the use of the double-underscore):

curl "https://www.courtlistener.com/api/rest/v4/people/?fields=educations__date_modified,educations__id"
{
  "educations": [
    {
      "id": 12856,
      "date_modified": "2023-03-31T07:15:28.556222-07:00",
    }
  ]
},
...
And to exclude the nested degree_detail field within each education entry:

curl "https://www.courtlistener.com/api/rest/v4/people/?omit=educations__degree_detail"
    {
      "resource_uri": "https://www.courtlistener.com/api/rest/v4/educations/12856/",
      "id": 12856,
      "school": {
        "resource_uri": "https://www.courtlistener.com/api/rest/v4/schools/4240/",
        "id": 4240,
        "is_alias_of": null,
        "date_created": "2010-06-07T17:00:00-07:00",
        "date_modified": "2010-06-07T17:00:00-07:00",
        "name": "University of Maine",
        "ein": 16000769
      },
      "person": "https://www.courtlistener.com/api/rest/v4/people/16214/",
      "date_created": "2023-03-31T07:15:28.556198-07:00",
      "date_modified": "2023-03-31T07:15:28.556222-07:00",
      "degree_level": "jd",
      "degree_year": 1979
    }
...
We highly recommend using this feature to optimize your requests.

Pagination
Most APIs can be paginated by using the page GET parameter, but that will be limited to 100 pages of results.

As of API v4, deep pagination is generally enabled for requests that are ordered by the id, date_modified, or date_created field. When sorting by these fields, the next and previous keys of the response are how you must paginate results, and the page parameter will not work.

Some API endpoints support slightly different fields for deep pagination:

/api/rest/v4/recap-fetch/ also supports the date_completed field.
/api/rest/v4/alerts/ and /api/rest/v4/docket-alerts/ only support the date_created field.
Rate Limits
Our APIs allow 5,000 queries per hour to authenticated users. Creating more than one account per project, person, or organization is forbidden. If you are in doubt, please contact us before creating multiple accounts.

To debug throttling issues:

Try browsing the API while logged into Courtlistener. If this works and your code fails, it usually means that your token authentication is not configured properly, and your code is getting throttled as an anonymous user, not according to your token.
Review your recent API usage by looking in your profile, but remember that it will show stats for the browsable API as well.
Review the authentication/throttling tips in our forum.
If, after checking the above, you need your rate limit increased, please get in touch so we can help.

Performance Tips
A few things to consider that may increase your performance:

Use field selection to limit the serialized payload and defer unused fields, reducing both payload size and database load, especially for large fields.

Avoid doing queries like court__id=xyz when you can instead do court=xyz. Doing queries with the extra __id introduces a join that can be expensive.

When using the search endpoint, smaller result sets are faster. It isn't always possible to tweak your query to return fewer results, but sometimes it is possible to do a more precise query first, thus making a broader query unnecessary. For example, a search for an individual in their expected jurisdiction will be faster than doing it in the entire corpus. This will benefit from profiling in your use case and application.

Advanced Field Definitions
Placing an HTTP OPTIONS request on an API is the best way to learn about its fields, but some fields require further explanation. Click below to learn about these fields.


APIs
Case Law APIs
We started collecting case law in 2009 and launched this API in 2013 as the first API for legal decisions.

Use this API to build your own collection of case law, complete complex legal research, and more.


PACER Data APIs
We have almost half a billion PACER-related objects in the RECAP Archive including dockets, entries, documents, parties, and attorneys. Use these APIs to access and understand this data.


RECAP APIs
Use these APIs to gather data from PACER and to share your PACER data with the public.


Pray and Pay API
Request PACER documents that are not yet available in the RECAP Archive. When another user purchases a document you've prayed for, you'll be notified automatically.

Use this API to programmatically create and manage prayer requests.


Search API
CourtListener allows you to search across hundreds of millions of items with advanced fields and operators. Use this API to automate the CourtListener search engine.


Judge APIs
Use these APIs to query and analyze thousands of federal and state court judges, including their biographical information, political affiliations, education and employment histories, and more.


Financial Disclosure APIs
All federal judges and many state judges must file financial disclosure documents to indicate any real or perceived biases they may have.

Use these APIs to work with this information.


Oral Argument APIs
CourtListener is home to the largest collection of oral argument recordings on the Internet. Use thees APIs to gather and analyze our collection.


Citation Lookup and Verification API
Use this API to look up citations in CourtListener's database of millions of citations.

This API can look up either an individual citation or can parse and look up every citation in a block of text. This can be useful as a guardrail to help prevent hallucinated citations.


Citation Network APIs
Use these APIs to traverse and analyze our network of citations between legal decisions.


Alert APIs
CourtListener is a scalable system for sending alerts by email or webhook based on search queries or for particular cases. Use these APIs to create, modify, list, and delete alerts.


Visualization APIs
To see and make Supreme Court case visualizations, use these APIs.
Legal Search API
/api/rest/v4/search/
Use this API to search case law, PACER data, judges, and oral argument audio recordings.

To get the most out of this API, see our coverage, advanced operators, and relative date queries documentation.

Basic Usage
This API uses the same GET parameters as the front end of the website. To use this API, place a search query on the front end of the website. That will give you a URL like:

https://www.courtlistener.com/q=foo
To make this into an API request, copy the GET parameters from this URL to the API endpoint, creating a request like:

curl -X GET \
  --header 'Authorization: Token <your-token-here>' \
  'https://www.courtlistener.com/api/rest/v4/search/?q=foo'
That returns:

{
  "count": 2343,
    "next": "https://www.courtlistener.com/api/rest/v4/search/?cursor=cz0yMzUuODcxMjUmcz04MDUzNTUzJnQ9byZkPTIwMjQtMDktMTY%3D&q=foo",
    "previous": null,
    "results": [
        {
            "absolute_url": "/opinion/6613686/foo-v-foo/",
            "attorney": "",
            "caseName": "Foo v. Foo",
            "caseNameFull": "Foo v. Foo",
            "citation": [
                "101 Haw. 235",
                "65 P.3d 182"
            ],
            "citeCount": 0,
            "cluster_id": 6613686,
            "court": "Hawaii Intermediate Court of Appeals",
            "court_citation_string": "Haw. App.",
            "court_id": "hawapp",
            "dateArgued": null,
            "dateFiled": "2003-01-10",
            "dateReargued": null,
            "dateReargumentDenied": null,
            "docketNumber": "24158",
            "docket_id": 63544014,
            "judge": "",
            "lexisCite": "",
            "meta": {
                "timestamp": "2024-06-22T10:26:35.320787Z",
                "date_created": "2022-06-26T23:24:18.926040Z",
                "score": {
                    "bm25": 2.1369965
                }
            },
            "neutralCite": "",
            "non_participating_judge_ids": [],
            "opinions": [
                {
                    "author_id": null,
                    "cites": [],
                    "download_url": null,
                    "id": 6489975,
                    "joined_by_ids": [],
                    "local_path": null,
                    "meta": {
                        "timestamp": "2024-06-24T21:14:41.408206Z",
                        "date_created": "2022-06-26T23:24:18.931912Z"
                    },
                    "per_curiam": false,
                    "sha1": "",
                    "snippet": "\nAffirmed in part, reversed in part, vacated and remanded\n",
                    "type": "lead-opinion"
                }
            ],
            "panel_ids": [],
            "panel_names": [],
            "posture": "",
            "procedural_history": "",
            "scdb_id": "",
            "sibling_ids": [
                6489975
            ],
            "source": "U",
            "status": "Published",
            "suitNature": "",
            "syllabus": ""
        },
    ...
That's the simple version. Read on to learn the rest.

Understanding the API
Unlike most APIs on CourtListener, this API is powered by our search engine, not our database.

This means that it does not use the same approach to ordering, filtering, or field definitions as our other APIs, and sending an HTTP OPTIONS request won't be useful.

CourtListener's search results are powered by the Citegeist Relevancy Engine, which supports both keyword search and semantic search.

Semantic search makes it possible to query the case law database using plain language queries, instead of keywords. It can be a better tool for untrained users, while keyword search provides a powerful ranking system with deep pagination that may be more familiar to attorneys.

For a deeper treatment of the pros and cons of these systems, please read our help page on Citegeist.

Semantic Search vs. Keyword Search
By default, API requests will be handled by our keyword search engine.

To use semantic search instead, special GET parameters or POST requests are needed. Whether to use GET or POST depends on the privacy requirements of your application:

GET — If you are able to send search queries to CourtListener, using a GET request is best and simplest.

To use semantic search with a GET request, add semantic=true to your request, and you will place a semantic query instead of a keyword query. It's that simple.

POST — If regulatory or privacy requirements prevent you from sending search queries to CourtListener — or if you just prefer a more private approach — we have another solution.

When you use a GET request, we receive the query, embed it on our system and calculate results. If you use a POST request, you can do the embedding in your system and send us only the resulting embedding, instead of sending the query.

To POST pre-computed embeddings to this endpoint, include a JSON body in the POST request:

{
  "embedding": [0.123, 0.456, -0.789, ...]
}
The embedding key in your request body is a list of floating-point numbers representing a vector of your query. It should have a length of 768 dimensions and is required for POST requests.

To calculate embeddings, we recommend our Inception microservice. For it to work properly, you will need to use our fine-tuned model.

Semantic search is only available for the case law search engine.

Setting the Result type
The most important parameter in this API is type. This parameter sets the type of object you are querying:

Type	Definition
o	Case law opinion clusters with nested Opinion documents.
r	List of Federal cases (dockets) with up to three nested documents. If there are more than three matching documents, the more_docs field for the docket result will be true.
rd	Federal filing documents from PACER
d	Federal cases (dockets) from PACER
p	Judges
oa	Oral argument audio files
For example, this query searches case law:

https://www.courtlistener.com/q=foo&type=o
And this query searches federal filings in the PACER system:

https://www.courtlistener.com/q=foo&type=r
If the type parameter is not provided, the default is to search case law.

Ordering Results
Each search type can be sorted by certain fields. These are available on the front end in the ordering drop down, which sets the order_by parameter.

Citegeist sorts results when you order by relevancy. It uses a combination of factors to provide the most important results first.

If your sorting field has null values, those results will be sorted at the end of the query, regardless of whether you sort in ascending or descending order. For example, if you sort by a date that is null for an opinion, that opinion will go at the end of the result set.

Filtering Results
Results can be filtered with the input boxes provided on the front end or by advanced query operators provided to the q parameter.

The best way to refine your query is to do so on the front end, and then copy the GET parameters to the API.

Fields
Unlike most of the fields on CourtListener, many fields on this API are provided in camelCase instead of snake_case. This is to make it easier for users to place queries like:

caseName:foo
Instead of:

case_name:foo
All available fields are listed on the advanced operators help page.

To understand the meaning of a field, find the object in our regular APIs that it corresponds to, and send an HTTP OPTIONS request to the API.

For example, the docketNumber field in the search engine corresponds to the docket_number field in the docket API, so an HTTP OPTIONS request to that API returns its definition:

curl -X OPTIONS \
  --header 'Authorization: Token <your-token-here>' \
  "https://www.courtlistener.com/api/rest/v4/dockets/" \
  | jq '.actions.POST.docket_number'
After filtering through jq, that returns:

{
  "type": "string",
  "required": false,
  "read_only": false,
  "label": "Docket number",
  "help_text": "The docket numbers of a case, can be consolidated and quite long. In some instances they are too long to be indexed by postgres and we store the full docket in the correction field on the Opinion Cluster."
}
Highlighting Results
To enhance performance, results are not highlighted by default. To enable highlighting, include highlight=on in your request.

When highlighting is disabled, the first 500 characters of snippet fields are returned for fields o, r, and rd.

Result Counts
type=d and type=r use cardinality aggregation to compute the result count. This enhances performance, but has an error of ±6% if results are over 2000. We recommend noting this in your interface by saying something like, "About 10,000 results."

Special Notes
A few fields deserve special consideration:

As in the front end, when the type is set to return case law, only published results are returned by default. To include unpublished and other statuses, you need to explicitly request them.

The snippet field contains the same values as are found on the front end. This uses the HTML5 <mark> element to identify up to five matches in a document.

This field only responds to arguments provided to the q parameter. If the q parameter is not used, the snippet field will show the first 500 characters of the text field.

This field only displays Opinion text content.

The meta field in main documents contains the score field, which is currently a JSON object that includes the bm25 score used by Elasticsearch to rank results. Additional scores may be introduced in the future.

Monitoring a Query for New Results
All query results are cached for ten minutes. This provides instant responses to front-end users who frequently refresh or paginate results.

Because of this, we do not recommend polling as a mechanism for monitoring queries for new results. Instead, use the Alert API, which will send emails or webhook events when there are new hits.


image.png