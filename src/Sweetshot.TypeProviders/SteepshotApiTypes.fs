namespace Sweetshot.TypeProviders

open FSharp.Data

module SteepshotApiTypes = 

    type Login = JsonProvider<"""
    {
        "username": "joseph.kalu"
    }
    """>

    type UserPosts = JsonProvider<"""
    {
      "count": 1,
      "next": null,
      "previous": null,
      "results": [
        {
          "body": "http://res.cloudinary.com/pmartynov/image/upload/v1483462873/ucy0ag1sk89zneyuzrgp.jpg",
          "title": "Test post Tue Jan  3 17:01:11 2017",
          "url": "/spam/@joseph.kalu/test-post-tue-jan--3-170111-2017",
          "category": "spam",
          "author": "joseph.kalu",
          "avatar": "",
          "author_rewards": 0,
          "author_reputation": 30,
          "net_votes": 4,
          "children": 0,
          "created": "2017-01-03T17:01:15Z",
          "curator_payout_value": 0.0,
          "total_payout_value": 0.0,
          "pending_payout_value": 0.0,
          "max_accepted_payout": 1000000.0,
          "total_payout_reward": 0.0,
          "vote": 0
        }
      ]
    }
    """>


