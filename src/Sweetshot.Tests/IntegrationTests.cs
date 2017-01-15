﻿using System;
using System.Configuration;
using System.IO;
using System.Linq;
using NUnit.Framework;
using Sweetshot.Library.HttpClient;
using Sweetshot.Library.Models.Common;
using Sweetshot.Library.Models.Requests;

namespace Sweetshot.Tests
{
    // check all tests
    // add more tests
    // check DTOs for all fields
    // specify types of all DTO fields
    // test all types of DTO fields
    // test (assert) errors

    // имена параметров брать из реквестов
    // поиск по категориям сделать тот же ответ как и вкатегоряих просто 
    // move endpoints name to config

    // для постов не обязателен sessionId
    // просмотреть карточки трелло

    [TestFixture]
    public class IntegrationTests
    {
        private const string Name = "joseph.kalu";
        private const string Password = "test1234";
        private const string NewPassword = "test12345";
        private string _sessionId = string.Empty;

        private readonly SteepshotApiClient _api = new SteepshotApiClient(ConfigurationManager.AppSettings["sweetshot_url"]);

        [OneTimeSetUp]
        public void Authenticate()
        {
            var request = new LoginRequest(Name, Password);
            _sessionId = _api.Login(request).Result.Result.SessionId;
        }

        [Test]
        public void Login_Valid_Credentials()
        {
            // Arrange
            var request = new LoginRequest(Name, Password);

            // Act
            var response = _api.Login(request).Result;

            // Assert
            AssertSuccessfulResult(response);
            Assert.IsNotEmpty(response.Result.Username);
            Assert.IsNotEmpty(response.Result.SessionId);
        }

        [Test]
        public void Login_Invalid_Credentials()
        {
            // Arrange
            var request = new LoginRequest(Name + "x", Password + "x");

            // Act
            var response = _api.Login(request).Result;

            // Assert
            AssertFailedResult(response);
            Assert.Contains("Unable to login with provided credentials.", response.Errors);
        }

        [Test]
        public void Login_Wrong_Password()
        {
            // Arrange
            var request = new LoginRequest(Name, Password + "x");

            // Act
            var response = _api.Login(request).Result;

            // Assert
            AssertFailedResult(response);
            Assert.Contains("Unable to login with provided credentials.", response.Errors);
        }

        [Test]
        public void Login_Wrong_Username()
        {
            // Arrange
            var request = new LoginRequest(Name + "x", Password);

            // Act
            var response = _api.Login(request).Result;

            // Assert
            AssertFailedResult(response);
            Assert.Contains("Unable to login with provided credentials.", response.Errors);
        }

        [Test]
        public void UserPosts()
        {
            // Arrange
            var request = new UserRequest(_sessionId, Name);

            // Act
            var response = _api.GetUserPosts(request).Result;

            // Assert
            AssertSuccessfulResult(response);
            Assert.IsTrue(response.Result.Count > 0);
            Assert.IsNotEmpty(response.Result.Results.First().Body);
            Assert.IsNotEmpty(response.Result.Results.First().Author);
        }

        [Test]
        public void UserPosts_Invalid_Username()
        {
            // Arrange
            var request = new UserRequest(_sessionId, Name + "x");

            // Act
            var response = _api.GetUserPosts(request).Result;

            // Assert
            AssertFailedResult(response);
        }

        [Test]
        public void Posts_Top()
        {
            // Arrange
            const int limit = 5;
            var request = new PostsRequest(_sessionId, PostType.Top, limit);

            // Act
            var response = _api.GetPosts(request).Result;

            // Assert
            AssertSuccessfulResult(response);
            Assert.IsTrue(response.Result.Results.Any());
        }

        [Test]
        public void Posts_Top_Check_Limit_Zero()
        {
            // Arrange
            var request = new PostsRequest(_sessionId, PostType.Top, 0);

            // Act
            var response = _api.GetPosts(request).Result;

            // Assert
            AssertSuccessfulResult(response);
            Assert.IsTrue(response.Result.Count == 10);
        }

        [Test]
        public void Posts_Top_Check_Limit_Negative()
        {
            // Arrange
            var request = new PostsRequest(_sessionId, PostType.Top, -10);

            // Act
            var response = _api.GetPosts(request).Result;

            // Assert
            AssertSuccessfulResult(response);
            Assert.IsTrue(response.Result.Count == 10);
        }

        [Test]
        public void Posts_Top_Check_Offset()
        {
            // Arrange
            var request = new PostsRequest(_sessionId, PostType.Top, 3, "/life/@hanshotfirst/best-buddies-i-see-you");

            // Act
            var response = _api.GetPosts(request).Result;

            // Assert
            AssertSuccessfulResult(response);
            Assert.IsTrue(response.Result.Count == 0);
        }

        [Test]
        public void Posts_Hot()
        {
            // Arrange
            const int limit = 5;
            var request = new PostsRequest(_sessionId, PostType.Hot, limit);

            // Act
            var response = _api.GetPosts(request).Result;

            // Assert
            AssertSuccessfulResult(response);
            Assert.IsTrue(response.Result.Results.Any());
        }

        [Test]
        public void Posts_New()
        {
            // Arrange
            const int limit = 5;
            var request = new PostsRequest(_sessionId, PostType.New, limit);

            // Act
            var response = _api.GetPosts(request).Result;

            // Assert
            AssertSuccessfulResult(response);
            Assert.IsTrue(response.Result.Results.Any());
        }

        // TODO Need to create a profile and test it
        [Test]
        public void Register()
        {
            // Arrange
            var request = new RegisterRequest("", "", "");

            // Act
            var response = _api.Register(request).Result;

            // Assert
            AssertSuccessfulResult(response);
            Assert.NotNull(response.Result.SessionId);
            Assert.NotNull(response.Result.Username);
        }

        [Test]
        public void Register_PostingKey_Invalid()
        {
            // Arrange
            var request = new RegisterRequest("5JdHigxo9s8rdNSfGteprcx1Fhi7SBUwb7e2UcNvnTdz18Si7s1", "anch1", "qwerty12345");

            // Act
            var response = _api.Register(request).Result;

            // Assert
            AssertFailedResult(response);
            Assert.Contains("posting_key Invalid posting key.", response.Errors);
        }

        [Test]
        public void Register_Username_Already_Exists()
        {
            // Arrange
            var request = new RegisterRequest("5JdHigxo9s8rdNSfGteprcx1Fhi7SBUwb7e2UcNvnTdz18Si7s1", "anch", "qwerty12345");

            // Act
            var response = _api.Register(request).Result;

            // Assert
            AssertFailedResult(response);
            Assert.Contains("username A user with that username already exists.", response.Errors);
        }

        [Test]
        public void Register_PostingKey_Same_With_New_Username()
        {
            // Arrange
            var request = new RegisterRequest("5JdHigxo9s8rdNSfGteprcx1Fhi7SBUwb7e2UcNvnTdz18Si7s1", "anch1", "qwerty12345");

            // Act
            var response = _api.Register(request).Result;

            // Assert
            //TODO check response message after fix
            Assert.Fail();
        }

        [Test]
        public void Register_PostingKey_Is_Blank()
        {
            // Arrange
            var request = new RegisterRequest("", "qweqweqweqwe", "qweqweqweqwe");

            // Act
            var response = _api.Register(request).Result;

            // Assert
            AssertFailedResult(response);
            Assert.Contains("posting_key This field may not be blank.", response.Errors);
        }

        [Test]
        public void Register_Password_Is_Short()
        {
            // Arrange
            var request = new RegisterRequest("5JdHsgxo9s8rdNsfGteprcxaFhi7SBUwb7e2UcNvnTdh18Si7so", "qweqweqweqwe", "qweqweq");

            // Act
            var response = _api.Register(request).Result;

            // Assert
            AssertFailedResult(response);
            Assert.Contains("password This password is too short. It must contain at least 8 characters.", response.Errors);
        }

        [Test]
        public void Register_Password_Is_Numeric()
        {
            // Arrange
            var request = new RegisterRequest("5JdHsgxo9s8rdNsfGteprcxaFhi7SBUwb7e2UcNvnTdh18Si7so", "qweqweqweqwe", "1234567890");

            // Act
            var response = _api.Register(request).Result;

            // Assert
            AssertFailedResult(response);
            Assert.Contains("password This password is entirely numeric.", response.Errors);
        }

        [Test]
        public void Vote_Up()
        {
            // Arrange
            var request = new VoteRequest(_sessionId, true, "/life/@hanshotfirst/best-buddies-i-see-you");

            // Act
            var response = _api.Vote(request).Result;

            // Assert
            AssertSuccessfulResult(response);
            Assert.NotNull(response.Result.NewTotalPayoutReward);
            Assert.True(response.Result.Status == "OK");
        }

        [Test]
        public void Vote_Up_Already_Voted()
        {
            // Arrange
            var request = new VoteRequest(_sessionId, true, "/spam/@joseph.kalu/test-post-tue-jan--3-170111-2017");

            // Act
            var response = _api.Vote(request).Result;

            // Assert
            AssertFailedResult(response);
            Assert.Contains("You have either used the maximum number of vote changes on this comment or performed the same action twice.", response.Errors);
        }

        [Test]
        public void Vote_Down()
        {
            // Arrange
            var request = new VoteRequest(_sessionId, false, "/life/@hanshotfirst/best-buddies-i-see-you");

            // Act
            var response = _api.Vote(request).Result;

            // Assert
            AssertSuccessfulResult(response);
            Assert.NotNull(response.Result.NewTotalPayoutReward);
            Assert.True(response.Result.Status == "OK");
        }

        [Test]
        public void Vote_Down_Already_Voted()
        {
            // Arrange
            var request = new VoteRequest(_sessionId, false, "/spam/@joseph.kalu/test-post-tue-jan--3-170111-2017");

            // Act
            var response = _api.Vote(request).Result;

            // Assert
            AssertFailedResult(response);
            Assert.Contains("You have either used the maximum number of vote changes on this comment or performed the same action twice.", response.Errors);
        }

        [Test]
        public void Vote_Empty_Identifier()
        {
            // Arrange
            var request = new VoteRequest(_sessionId, true, "");

            // Act
            var response = _api.Vote(request).Result;

            // Assert
            AssertFailedResult(response);
            Assert.Contains(@"Method ""POST"" not allowed.", response.Errors);
        }

        [Test]
        public void Vote_Invalid_Identifier1()
        {
            // Arrange
            var request = new VoteRequest(_sessionId, true, "qwe");

            // Act
            var response = _api.Vote(request).Result;

            // Assert
            AssertFailedResult(response);
            Assert.Contains("Internal Server Error", response.Errors);
        }

        [Test]
        public void Vote_Invalid_Identifier2()
        {
            // Arrange
            var request = new VoteRequest(_sessionId, true, "qwe/qwe");

            // Act
            var response = _api.Vote(request).Result;

            // Assert
            AssertFailedResult(response);
            Assert.Contains("Internal Server Error", response.Errors);
        }

        [Test]
        public void Vote_Invalid_Identifier3()
        {
            // Arrange
            var request = new VoteRequest(_sessionId, true, "/qwe/qwe");

            // Act
            var response = _api.Vote(request).Result;

            // Assert
            AssertFailedResult(response);
            Assert.Contains("Internal Server Error", response.Errors);
        }

        [Test]
        public void Vote_Invalid_Identifier4()
        {
            // Arrange
            var request = new VoteRequest(_sessionId, true, "/qwe/@qwe");

            // Act
            var response = _api.Vote(request).Result;

            // Assert
            AssertFailedResult(response);
            Assert.Contains("identifier Invalid identifier", response.Errors);
        }

        [Test]
        public void Vote_Invalid_Identifier5()
        {
            // Arrange
            var request = new VoteRequest(_sessionId, true, "/qwe/@qwe/");

            // Act
            var response = _api.Vote(request).Result;

            // Assert
            AssertFailedResult(response);
            Assert.Contains("You have either used the maximum number of vote changes on this comment or performed the same action twice.", response.Errors);
        }

        [Test]
        public void Follow()
        {
            // Arrange
            var request = new FollowRequest(_sessionId, FollowType.Follow, "asduj");

            // Act
            var response = _api.Follow(request).Result;

            // Assert
            AssertSuccessfulResult(response);
        }

        [Test]
        public void Follow_UnFollow()
        {
            // Arrange
            var request = new FollowRequest(_sessionId, FollowType.UnFollow, "asduj");

            // Act
            var response = _api.Follow(request).Result;

            // Assert
            AssertSuccessfulResult(response);
        }

        [Test]
        public void Follow_Invalid_Username()
        {
            // Arrange
            var request = new FollowRequest(_sessionId, FollowType.Follow, "qwet32qwe3qwewe");

            // Act
            var response = _api.Follow(request).Result;

            // Assert
            // TODO System should return an error in case of invalid username.
            Assert.Fail();
        }

        [Test]
        public void Follow_Empty_Username()
        {
            // Arrange
            var request = new FollowRequest(_sessionId, FollowType.Follow, "");

            // Act
            var response = _api.Follow(request).Result;

            // Assert
            AssertFailedResult(response);
            Assert.Contains(@"Method ""POST"" not allowed.", response.Errors);
        }

        [Test]
        public void Comments()
        {
            // Arrange
            var request = new GetCommentsRequest(_sessionId, "@asduj/new-application-coming---");

            // Act
            var response = _api.GetComments(request).Result;

            // Assert
            AssertSuccessfulResult(response);
            Assert.IsTrue(response.Result.Comments.Any());
        }

        [Test]
        public void Comments_Empty_Url()
        {
            // Arrange
            var request = new GetCommentsRequest(_sessionId, "");

            // Act
            var response = _api.GetComments(request).Result;

            // Assert
            AssertFailedResult(response);
            Assert.Contains("Wrong identifier.", response.Errors);
        }

        [Test]
        public void Comments_Invalid_Url()
        {
            // Arrange
            var request = new GetCommentsRequest(_sessionId, "qwe");

            // Act
            var response = _api.GetComments(request).Result;

            // Assert
            AssertFailedResult(response);
            Assert.Contains("Wrong identifier.", response.Errors);
        }

        [Test]
        public void Comments_Invalid_Url_But_Valid_User()
        {
            // Arrange
            var request = new GetCommentsRequest(_sessionId, "@asduj/qweqweqweqw");

            // Act
            var response = _api.GetComments(request).Result;

            // Assert
            AssertSuccessfulResult(response);
            Assert.IsFalse(response.Result.Comments.Any());
        }

        [Test]
        public void CreateComment()
        {
            // Arrange
            var request = new CreateCommentsRequest(_sessionId, "/spam/@joseph.kalu/test-post-127", "хипстеры наелись фалафели в коворкинге", "свитшот");

            // Act
            var response = _api.CreateComment(request).Result;

            // Assert
            AssertSuccessfulResult(response);
        }

        [Test]
        public void CreateComment_Wrong_Identifier()
        {
            // Arrange
            var request = new CreateCommentsRequest(_sessionId, "@asduj/new-application-coming---", "хипстеры наелись фалафели в коворкинге", "свитшот");

            // Act
            var response = _api.CreateComment(request).Result;

            // Assert
            AssertFailedResult(response);
            Assert.Contains("Wrong identifier.", response.Errors);
        }

        [Test]
        public void CreateComment_Empty_Url()
        {
            // Arrange
            var request = new CreateCommentsRequest(_sessionId, "", "хипстеры наелись фалафели в коворкинге", "свитшот");

            // Act
            var response = _api.CreateComment(request).Result;

            // Assert
            AssertFailedResult(response);
            Assert.Contains("Method \"POST\" not allowed.", response.Errors);
        }

        [Test]
        public void CreateComment_Empty_Body()
        {
            // Arrange
            var request = new CreateCommentsRequest(_sessionId, "/spam/@joseph.kalu/test-post-127", "", "свитшот");

            // Act
            var response = _api.CreateComment(request).Result;

            // Assert
            AssertFailedResult(response);
            Assert.Contains("body This field may not be blank.", response.Errors);
        }

        [Test]
        public void CreateComment_Empty_Title()
        {
            // Arrange
            var request = new CreateCommentsRequest(_sessionId, "/spam/@joseph.kalu/test-post-127", "свитшот", "");

            // Act
            var response = _api.CreateComment(request).Result;

            // Assert
            AssertFailedResult(response);
            Assert.Contains("title This field may not be blank.", response.Errors);
        }

        [Test]
        public void Upload()
        {
            // Arrange
            var path = Path.Combine(AppDomain.CurrentDomain.BaseDirectory, @"Data\cat.jpg");
            var file = File.ReadAllBytes(path);
            var request = new UploadImageRequest(_sessionId, "cat", file, "cat1", "cat2", "cat3", "cat4");

            // Act
            var response = _api.Upload(request).Result;

            // Assert
            AssertSuccessfulResult(response);
            Assert.NotNull(response.Result.Body);
            Assert.NotNull(response.Result.Title);
            Assert.IsNotEmpty(response.Result.Tags);
        }

        [Test]
        public void Categories()
        {
            // Arrange
            var request = new CategoriesRequest(_sessionId);

            // Act
            var response = _api.GetCategories(request).Result;

            // Assert
            AssertSuccessfulResult(response);
            Assert.NotNull(response.Result);
            Assert.IsNotEmpty(response.Result.Results);
        }

        [Test]
        public void Categories_Offset()
        {
            // Arrange
            var request = new CategoriesRequest(_sessionId, "food");

            // Act
            var response = _api.GetCategories(request).Result;

            // Assert
            AssertSuccessfulResult(response);
            Assert.NotNull(response.Result);
            Assert.IsNotEmpty(response.Result.Results);
        }

        [Test]
        public void Categories_Offset_Empty()
        {
            // Arrange
            var request = new CategoriesRequest(_sessionId, " ");

            // Act
            var response = _api.GetCategories(request).Result;

            // Assert
            AssertSuccessfulResult(response);
            Assert.NotNull(response.Result);
            Assert.IsNotEmpty(response.Result.Results);
        }

        [Test]
        public void Categories_Offset_Not_Exisiting()
        {
            // Arrange
            var request = new CategoriesRequest(_sessionId, "qweqweqwe");

            // Act
            var response = _api.GetCategories(request).Result;

            // Assert
            AssertSuccessfulResult(response);
            Assert.NotNull(response.Result);
            Assert.IsNotEmpty(response.Result.Results);
        }

        [Test]
        public void Categories_Search()
        {
            // Arrange
            var request = new SearchCategoriesRequest(_sessionId, "foo");

            // Act
            var response = _api.SearchCategories(request).Result;

            // Assert
            AssertSuccessfulResult(response);
            Assert.NotNull(response.Result);
            Assert.IsNotEmpty(response.Result.Results);
        }

        [Test]
        public void Categories_Search_Invalid_Query()
        {
            // Arrange
            var request = new SearchCategoriesRequest(_sessionId, "qwerqwerqwerqwerqwerqwerqwerqwer");

            // Act
            var response = _api.SearchCategories(request).Result;

            // Assert
            AssertSuccessfulResult(response);
            Assert.NotNull(response.Result);
            Assert.IsEmpty(response.Result.Results);
        }

        [Test]
        public void Categories_Search_Short_Query()
        {
            // Arrange
            var request = new SearchCategoriesRequest(_sessionId, "fo");

            // Act
            var response = _api.SearchCategories(request).Result;

            // Assert
            AssertSuccessfulResult(response);
            Assert.NotNull(response.Result);
            Assert.IsEmpty(response.Result.Results);
        }

        [Test]
        public void ChangePassword()
        {
            // Arrange
            var request = new ChangePasswordRequest(_sessionId, Password, NewPassword);

            // Act
            var response = _api.ChangePassword(request).Result;

            // Assert
            AssertSuccessfulResult(response);
            Assert.AreEqual("OK", response.Result.Status);

            // Revert
            var loginResponse = _api.Login(new LoginRequest(Name, NewPassword)).Result;
            var response2 = _api.ChangePassword(new ChangePasswordRequest(loginResponse.Result.SessionId, NewPassword, Password)).Result;
            AssertSuccessfulResult(response2);
            Assert.AreEqual("OK", response2.Result.Status);
        }

        [Test]
        public void ChangePassword_Invalid_OldPassword()
        {
            // Arrange
            var request = new ChangePasswordRequest(_sessionId, Password + "x", NewPassword);

            // Act
            var response = _api.ChangePassword(request).Result;

            // Assert
            AssertFailedResult(response);
            Assert.Contains("old_password Old password is invalid.", response.Errors);
        }

        // TODO Add more tests about password types
        [Test]
        public void ChangePassword_NewPassword_Short()
        {
            // Arrange
            var request = new ChangePasswordRequest(_sessionId, Password, "t");

            // Act
            var response = _api.ChangePassword(request).Result;

            // Assert
            AssertFailedResult(response);
            Assert.Contains("new_password This password is too short. It must contain at least 8 characters.", response.Errors);
        }

        [Test]
        public void ChangePassword_Invalid_SessionId()
        {
            // Arrange
            var request = new ChangePasswordRequest(_sessionId + "x", Password, NewPassword);

            // Act
            var response = _api.ChangePassword(request).Result;

            // Assert
            AssertFailedResult(response);
            Assert.Contains("Authentication credentials were not provided.", response.Errors);
        }

        // TODO Update this one after fix from backend
        // TODO Discuss do we need it
        [Test]
        public void Logout()
        {
            // Arrange
            var request = new LogoutRequest(_sessionId);

            // Act
            var response = _api.Logout(request).Result;

            // Assert
            AssertSuccessfulResult(response);
        }

        [Test]
        public void UserProfile()
        {
            // Arrange
            var request = new UserRequest(_sessionId, Name);

            // Act
            var response = _api.GetUserProfile(request).Result;

            // Assert
            AssertSuccessfulResult(response);
            Assert.NotNull(response.Result.Username);
        }

        [Test]
        public void UserProfile_Invalid_Username()
        {
            // Arrange
            var request = new UserRequest(_sessionId, "qweqweqwe");

            // Act
            var response = _api.GetUserProfile(request).Result;

            // Assert
            AssertFailedResult(response);
            Assert.Contains("<h1>Server Error (500)</h1>", response.Errors);
        }

        [Test]
        public void UserFriends_Followers()
        {
            // Arrange
            var request = new UserFriendsRequest(_sessionId, Name, FriendsType.Followers);

            // Act
            var response = _api.GetUserFriends(request).Result;

            // Assert
            AssertSuccessfulResult(response);
            Assert.NotNull(response.Result.Count);
            Assert.NotNull(response.Result.Offset);
            Assert.IsNotEmpty(response.Result.Results);
        }

        [Test]
        public void UserFriends_Following()
        {
            // Arrange
            var request = new UserFriendsRequest(_sessionId, Name, FriendsType.Following);

            // Act
            var response = _api.GetUserFriends(request).Result;

            // Assert
            AssertSuccessfulResult(response);
            Assert.NotNull(response.Result.Count);
            Assert.NotNull(response.Result.Offset);
            Assert.IsNotEmpty(response.Result.Results);
        }

        [Test]
        public void UserFriends_Following_Invalid_Username()
        {
            // Arrange
            var request = new UserFriendsRequest(_sessionId, Name + "x", FriendsType.Following);

            // Act
            var response = _api.GetUserFriends(request).Result;

            // Assert
            AssertSuccessfulResult(response);
            Assert.NotNull(response.Result.Count == 0);
            Assert.IsEmpty(response.Result.Results);
        }

        [Test]
        public void UserFriends_Following_Offset()
        {
            // Arrange
            var request = new UserFriendsRequest(_sessionId, Name, FriendsType.Following, "vivianupman");

            // Act
            var response = _api.GetUserFriends(request).Result;

            // Assert
            AssertSuccessfulResult(response);
            Assert.NotNull(response.Result.Count);
            Assert.NotNull(response.Result.Offset);
            Assert.IsNotEmpty(response.Result.Results);
        }

        private void AssertSuccessfulResult<T>(OperationResult<T> response)
        {
            Assert.NotNull(response);
            Assert.IsTrue(response.Success);
            Assert.NotNull(response.Result);
            Assert.IsEmpty(response.Errors);
        }

        private void AssertFailedResult<T>(OperationResult<T> response)
        {
            Assert.NotNull(response);
            Assert.IsFalse(response.Success);
            Assert.IsNull(response.Result);
            Assert.IsNotEmpty(response.Errors);
        }
    }
}