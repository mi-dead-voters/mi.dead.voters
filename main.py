from bs4 import BeautifulSoup, NavigableString, Tag
import asyncio
import aiohttp

from utility import *

async def scrape_voter(session, voter_details):
    try:
        url = "https://mvic.sos.state.mi.us/Voter/SearchByName"
        voter_details = voter_details.rstrip()
        fname, lname, year, zipcode = voter_details.split(',')

        # find the month because whoever made the dataset is retarded and didn't include it
        for month in range(1,13):
            body = {
                "FirstName": fname,
                "LastName": lname,
                "NameBirthMonth": month,
                "NameBirthYear": year,
                "ZipCode": zipcode,
                "Dln": "",
                "DlnBirthMonth": 0,
                "DlnBirthYear": "",
                "DpaID": 0,
                "Months": None,
                "VoterNotFound": False,
                "TransitionVoter": False
            }

            async with session.post(url=url, data=body) as response:
                html = await response.text()
                soup = BeautifulSoup(html, 'lxml')

                absentee_info = soup.find(id="lblAbsenteeVoterInformation")
                if absentee_info is not None:
                    # archive the raw html
                    voter_info = f"{fname},{lname},{month},{year},{zipcode}"
                    with open(f"html_archive\\{voter_info.replace(',','_')}.html", "w") as html_file:
                        html_file.write(html)

                    # check if application for ballot was received
                    ballot_info = []
                    app_received = absentee_info.find("b", string="Application received")
                    if app_received:
                        for br in absentee_info.findAll('br'):
                            next_s = br.nextSibling
                            if not (next_s and isinstance(next_s, NavigableString)):
                                continue

                            text = str(next_s).strip()
                            if text:
                                ballot_info.append(text)

                    result = {
                        "FirstName": fname,
                        "LastName": lname,
                        "BirthMonth": month,
                        "BirthYear": year,
                        "ZipCode": zipcode,
                        "Voted": False
                    }
                    if len(ballot_info) > 0:
                        result["ElectionDate"] = ballot_info[0]
                        result["ApplicationReceived"] = ballot_info[1]
                        result["BallotSent"] = ballot_info[2]
                        result["BallotReceived"] = ballot_info[3]
                        result["Voted"] = True

                    print(result)
                    return result

    except Exception as e:
        print(e)


async def scrape_async(voters, loop):
    async with aiohttp.ClientSession(loop=loop) as session:
        response = await asyncio.gather(*[scrape_voter(session, line) for line in voters], return_exceptions=True)
        return response


def scrape():
    # do in batches
    batches = read_file("detroit_index.txt", 100)

    registered_dead_voters = []
    dead_voters_who_voted = []
    loop = asyncio.get_event_loop()
    for batch in batches:
        responses = loop.run_until_complete(scrape_async(batch, loop))
        registered_dead_voters += [voter for voter in responses if voter is not None]
        dead_voters_who_voted += [voter for voter in registered_dead_voters if voter["Voted"]]

        # output
        stats = dump_stats(registered_dead_voters, dead_voters_who_voted)
        dump_info(dead_voters_who_voted, "dead_voters_who_voted.json")
        dump_info(registered_dead_voters, "registered_dead_voters.json")

    return stats


if __name__ == "__main__":
    try:
        print("SCRAPING DEAD VOTERS...")

        stats = scrape()

        print("SUCCESS!")
        print(stats)
    except Exception as e:
        print(e)