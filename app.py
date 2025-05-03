import streamlit as st
from serpapi import GoogleSearch
import time

st.title("Ad-Spending Business Finder (Fixed Search Method)")

# Input fields
business_type = st.text_input("Business Type (e.g., HVAC, landscaper)", "")
city = st.text_input("City and State (e.g., Pasadena, CA)", "")
api_key = st.secrets["serpapi_key"]

def get_lat_lng_from_maps(city_query, api_key):
    search = GoogleSearch({
        "engine": "google_maps",
        "type": "search",
        "q": city_query,
        "api_key": api_key
    })
    result = search.get_dict()
    if "local_results" in result and result["local_results"]:
        coords = result["local_results"][0].get("gps_coordinates")
        if coords:
            lat = coords.get("latitude")
            lng = coords.get("longitude")
            return f"@{lat},{lng},14z"
    return None

if business_type and city:
    st.info("Getting location coordinates...")

    ll_value = get_lat_lng_from_maps(city, api_key)

    # Fallback coordinates if lookup fails
    fallback_ll = {
        "pasadena, ca": "@34.1478,-118.1445,14z",
        "los angeles, ca": "@34.0522,-118.2437,14z",
        "san diego, ca": "@32.7157,-117.1611,14z"
    }
    if not ll_value:
        key = city.strip().lower()
        ll_value = fallback_ll.get(key)
        if ll_value:
            st.warning("Falling back to default coordinates for this city.")
        else:
            st.error("Could not determine location coordinates. Try a more specific or nearby city.")

    if ll_value:
        st.success(f"Coordinates used: {ll_value}")
        st.info("Scraping Google Maps...")

        query = f"{business_type} in {city}"
        all_results = []
        page = 0
        has_next = True

        while has_next:
            st.write(f"Scraping page {page + 1}...")

            params = {
                "engine": "google_maps",
                "type": "search",
                "q": query,
                "api_key": api_key,
                "start": page * 20,
                "ll": ll_value
            }

            search = GoogleSearch(params)
            results = search.get_dict()
            local_results = results.get("local_results", [])

            st.write(f"Found {len(local_results)} results on page {page + 1}")
            if not local_results:
                break

            all_results.extend(local_results)
            page += 1
            has_next = "serpapi_pagination" in results

            time.sleep(1.5)

        st.write(f"**Total businesses scraped:** {len(all_results)}")

        with_websites = [b for b in all_results if "website" in b]
        st.write(f"**Businesses with websites:** {len(with_websites)}")

        advertised = []
        for idx, biz in enumerate(with_websites):
            domain = biz["website"].replace("https://", "").replace("http://", "").split("/")[0]
            st.write(f"Checking ads for {domain} ({idx + 1} of {len(with_websites)})")

            ad_params = {
                "engine": "google_ads_transparency",
                "q": domain,  # Correct search method: use "q" instead of "advertiser_id"
                "api_key": api_key
            }

            ad_search = GoogleSearch(ad_params)
            ad_data = ad_search.get_dict()

            if "ad_data" in ad_data and ad_data["ad_data"]:
                advertised.append({
                    "name": biz.get("title"),
                    "website": biz.get("website"),
                    "domain": domain
                })

            time.sleep(1.5)

        st.write(f"**Advertisers found in last 30 days:** {len(advertised)}")

        if advertised:
            st.dataframe(advertised)
        else:
            st.warning("No advertisers found recently.")
