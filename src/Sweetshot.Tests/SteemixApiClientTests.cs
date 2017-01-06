using System.IO;
using System.Linq;
using NUnit.Framework;
using Sweetshot.Library.HttpClient;
using Sweetshot.Library.Models.Requests;

namespace Sweetshot.Tests
{
    // F# providers
    // async \ await
    // more tests
    // move setting to config
    // new method in API
    // check DTOs for all fields

    [TestFixture]
    public class SteemixApiClientTests
    {
        private const string Name = "joseph.kalu";
        private const string Password = "test1234";
        private string _sessionId = string.Empty;

        private readonly SteepshotApiClient _api = new SteepshotApiClient();

        [OneTimeSetUp]
        public void Setup()
        {
            var request = new LoginRequest(Name, Password);
            _sessionId = _api.Login(request).Result.Result.SessionId;
        }

        [Test]
        public void LoginTest_Valid_Credentials()
        {
            // Arrange
            var request = new LoginRequest(Name, Password);

            // Act
            var response = _api.Login(request).Result;

            // Assert
            Assert.NotNull(response);
            Assert.IsTrue(response.Success);
            Assert.IsNull(response.Error);
            Assert.NotNull(response.Result);

            Assert.IsNotEmpty(response.Result.Username);
            Assert.IsNotEmpty(response.Result.SessionId);
        }

        [Test]
        public void LoginTest_Invalid_Credentials()
        {
            // Arrange
            var request = new LoginRequest(Name + "x", Password + "x");

            // Act
            var response = _api.Login(request).Result;

            // Assert
            Assert.NotNull(response);
            Assert.IsFalse(response.Success);
            Assert.IsNull(response.Result);
            Assert.IsNotEmpty(response.Error);

            Assert.AreEqual("Unable to login with provided credentials.", response.Error);
        }

        [Test]
        public void LoginTest_Wrong_Password()
        {
            // Arrange
            var request = new LoginRequest(Name, Password + "x");

            // Act
            var response = _api.Login(request).Result;

            // Assert
            Assert.NotNull(response);
            Assert.IsFalse(response.Success);
            Assert.IsNull(response.Result);
            Assert.IsNotEmpty(response.Error);

            Assert.AreEqual("Unable to login with provided credentials.", response.Error);
        }

        [Test]
        public void LoginTest_Wrong_Username()
        {
            // Arrange
            var request = new LoginRequest(Name + "x", Password);

            // Act
            var response = _api.Login(request).Result;

            // Assert
            Assert.NotNull(response);
            Assert.IsFalse(response.Success);
            Assert.IsNull(response.Result);
            Assert.IsNotEmpty(response.Error);

            Assert.AreEqual("Unable to login with provided credentials.", response.Error);
        }

        [Test]
        public void GetUserPostsTest_ValidParameters()
        {
            // Arrange
            var request = new UserPostRequest(_sessionId, Name);

            // Act
            var response = _api.GetUserPosts(request).Result;

            // Assert
            Assert.NotNull(response);
            Assert.IsTrue(response.Success);
            Assert.IsNull(response.Error);
            Assert.NotNull(response.Result);

            Assert.IsTrue(response.Result.Count > 0);
            Assert.IsNotEmpty(response.Result.Results.First().Body);
            Assert.IsNotEmpty(response.Result.Results.First().Author);
        }

        [Test]
        public void GetUserPostsTest_Invalid_Username()
        {
            // Arrange
            var request = new UserPostRequest(_sessionId, Name + "x");

            // Act
            var response = _api.GetUserPosts(request).Result;

            // Assert
            Assert.NotNull(response);
            Assert.IsFalse(response.Success);
            Assert.IsNull(response.Result);
            Assert.IsNotEmpty(response.Error);
        }





        [Test]
        public void GetTopPostsTest()
        {
            // Arrange
            var request = new TopPostRequest(_sessionId, 10, 10);

            // Act
            var response = _api.GetTopPosts(request);

            // Assert
            Assert.NotNull(response);
            Assert.IsTrue(response.Result.Result.Count > 0);
        }

        [Test]
        public void UploadImageTest()
        {
            // Arrange
            var file = File.ReadAllBytes(@"/home/anch/Pictures/cats.jpg");
            var request = new UploadImageRequest(_sessionId, "Cats", file);

            // Act
            var response = _api.Upload(request).Result;

            // Assert
            Assert.NotNull(response);
        }

        [Test]
        public void UpVoteTest_PostArchived()
        {
            // Arrange
            var request = new VoteRequest(_sessionId, "@shenanigator/if-you-want-jobs-take-away-their-shovels-and-give-them-spoons");

            // Act
            var response = _api.UpVote(request).Result;

            // Assert
            Assert.NotNull(response);
            Assert.IsFalse(response.Result.IsVoted);
        }

        [Test]
        public void DownVoteTest_PostArchived()
        {
            // Arrange
            var request = new VoteRequest(_sessionId, "@shenanigator/if-you-want-jobs-take-away-their-shovels-and-give-them-spoons");

            // Act
            var response = _api.DownVote(request).Result;

            // Assert
            Assert.NotNull(response);
            Assert.IsFalse(response.Result.IsVoted);
        }

        [Test]
        public void RegisterTest()
        {
            // Arrange
            var request = new RegisterRequest("5JdHigxo9s8rdNSfGteprcx1Fhi7SBUwb7e2UcNvnTdz18Si7so", "anch", "qwerty12345");

            // Act

            var response = _api.Register(request).Result;

            // Assert
            Assert.NotNull(response);
            Assert.IsNotEmpty(response.Result.username);
        }

        [Test]
        public void GetCommentsTest()
        {
            // Arrange
            var request = new GetCommentsRequest(_sessionId, "@asduj/new-application-coming---");

            // Act
            var response = _api.GetComments(request).Result;

            // Assert
            Assert.NotNull(response);
            Assert.IsTrue(response.Result.comments.Length > 0);
        }


        [Test]
        public void CreateCommentTest()
        {
            // Arrange
            var request = new CreateCommentsRequest(_sessionId, "@asduj/new-application-coming---", "люк я твой отец", "лошта?");

            // Act
            var response = _api.CreateComment(request).Result;

            // Assert
            Assert.NotNull(response);
        }

        [Test]
        public void FollowTest()
        {
            // Arrange
            var request = new FollowRequest(_sessionId, "asduj");

            // Act
            var response = _api.Follow(request).Result;

            // Assert
            Assert.NotNull(response);
        }

        [Test]
        public void UnfollowTest()
        {
            // Arrange
            var request = new FollowRequest(_sessionId, "asduj");

            // Act
            var response = _api.Unfollow(request).Result;

            // Assert
            Assert.NotNull(response);
        }
    }
}