using System;
using NUnit.Framework;
using Sweetshot.Library.Models.Requests;
using Sweetshot.Library.Models.Requests.Common;

namespace Sweetshot.Tests
{
    [TestFixture]
    public class UnitTests
    {
        [Test]
        public void Vote_Empty_Identifier()
        {
            var ex = Assert.Throws<ArgumentNullException>(() =>
            {
                var r = new VoteRequest("sessionId", true, "");
            });
            Assert.That(ex.ParamName, Is.EqualTo("identifier"));
        }

        [Test]
        public void Follow_Empty_Username()
        {
            var ex = Assert.Throws<ArgumentNullException>(() =>
            {
                var r = new FollowRequest("sessionId", FollowType.Follow, "");
            });
            Assert.That(ex.ParamName, Is.EqualTo("username"));
        }

        [Test]
        public void Comments_Empty_Url()
        {
            var ex = Assert.Throws<ArgumentNullException>(() =>
            {
                var r = new GetCommentsRequest("sessionId", "");
            });
            Assert.That(ex.ParamName, Is.EqualTo("url"));
        }

        [Test]
        public void CreateComment_Empty_Url()
        {
            var ex = Assert.Throws<ArgumentNullException>(() =>
            {
                var r = new CreateCommentsRequest("sessionId", "", "test", "test");
            });
            Assert.That(ex.ParamName, Is.EqualTo("url"));
        }

        [Test]
        public void OffsetLimitFields_Zero_Limit()
        {
            var ex = Assert.Throws<ArgumentNullException>(() =>
            {
                var r = new OffsetLimitFields("test", 0);
            });
            Assert.That(ex.ParamName, Is.EqualTo("limit"));
        }

        [Test]
        public void OffsetLimitFields_Empty_Offset()
        {
            var ex = Assert.Throws<ArgumentNullException>(() =>
            {
                var r = new OffsetLimitFields("", 10);
            });
            Assert.That(ex.ParamName, Is.EqualTo("offset"));
        }

        [Test]
        public void UserFriendsRequest_Zero_Limit()
        {
            var ex = Assert.Throws<ArgumentNullException>(() =>
            {
                var r = new UserFriendsRequest("username", FriendsType.Followers, "offset");
            });
            Assert.That(ex.ParamName, Is.EqualTo("limit"));
        }

        [Test]
        public void UserFriendsRequest_Empty_Offset()
        {
            var ex = Assert.Throws<ArgumentNullException>(() =>
            {
                var r = new UserFriendsRequest("username", FriendsType.Followers, "", 10);
            });
            Assert.That(ex.ParamName, Is.EqualTo("offset"));
        }

        [Test]
        public void CategoriesRequest_Zero_Limit()
        {
            var ex = Assert.Throws<ArgumentNullException>(() =>
            {
                var r = new CategoriesRequest("test", 0);
            });
            Assert.That(ex.ParamName, Is.EqualTo("limit"));
        }

        [Test]
        public void CategoriesRequest_Empty_Offset()
        {
            var ex = Assert.Throws<ArgumentNullException>(() =>
            {
                var r = new CategoriesRequest("", 10);
            });
            Assert.That(ex.ParamName, Is.EqualTo("offset"));
        }

        [Test]
        public void SearchCategoriesRequest_Zero_Limit()
        {
            var ex = Assert.Throws<ArgumentNullException>(() =>
            {
                var r = new SearchCategoriesRequest("query", "test", 0);
            });
            Assert.That(ex.ParamName, Is.EqualTo("limit"));
        }

        [Test]
        public void SearchCategoriesRequest_Empty_Offset()
        {
            var ex = Assert.Throws<ArgumentNullException>(() =>
            {
                var r = new SearchCategoriesRequest("query", "", 10);
            });
            Assert.That(ex.ParamName, Is.EqualTo("offset"));
        }
    }
}