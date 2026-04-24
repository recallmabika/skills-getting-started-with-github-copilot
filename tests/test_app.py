"""Comprehensive tests for the Mergington High School API."""

import pytest


class TestRootEndpoint:
    """Tests for the root endpoint."""

    def test_root_redirects_to_static(self, client):
        """Test that root endpoint redirects to /static/index.html."""
        response = client.get("/", follow_redirects=False)
        assert response.status_code == 307
        assert "/static/index.html" in response.headers["location"]


class TestGetActivities:
    """Tests for the GET /activities endpoint."""

    def test_get_activities_returns_all(self, client, reset_activities):
        """Test that all activities are returned."""
        response = client.get("/activities")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 9
        assert "Chess Club" in data
        assert "Programming Class" in data

    def test_get_activities_structure(self, client, reset_activities):
        """Test that activities have correct structure."""
        response = client.get("/activities")
        data = response.json()
        activity = data["Chess Club"]
        
        assert "description" in activity
        assert "schedule" in activity
        assert "max_participants" in activity
        assert "participants" in activity
        assert isinstance(activity["participants"], list)

    def test_get_activities_contains_participants(self, client, reset_activities):
        """Test that activities contain correct initial participants."""
        response = client.get("/activities")
        data = response.json()
        
        assert "michael@mergington.edu" in data["Chess Club"]["participants"]
        assert "emma@mergington.edu" in data["Programming Class"]["participants"]


class TestSignupForActivity:
    """Tests for the POST /activities/{activity_name}/signup endpoint."""

    def test_signup_success(self, client, reset_activities):
        """Test successful signup for an activity."""
        response = client.post(
            "/activities/Chess Club/signup?email=newemail@mergington.edu"
        )
        assert response.status_code == 200
        data = response.json()
        assert "Signed up" in data["message"]
        assert "newemail@mergington.edu" in data["message"]

    def test_signup_adds_participant(self, client, reset_activities):
        """Test that signup actually adds a participant."""
        email = "student@mergington.edu"
        client.post(f"/activities/Chess Club/signup?email={email}")
        
        response = client.get("/activities")
        activities = response.json()
        assert email in activities["Chess Club"]["participants"]

    def test_signup_nonexistent_activity(self, client, reset_activities):
        """Test signup for non-existent activity returns 404."""
        response = client.post(
            "/activities/Fake Activity/signup?email=test@mergington.edu"
        )
        assert response.status_code == 404
        assert "Activity not found" in response.json()["detail"]

    def test_signup_already_signed_up(self, client, reset_activities):
        """Test that duplicate signup returns 400."""
        email = "michael@mergington.edu"  # Already in Chess Club
        response = client.post(f"/activities/Chess Club/signup?email={email}")
        assert response.status_code == 400
        assert "already signed up" in response.json()["detail"]

    def test_signup_multiple_activities(self, client, reset_activities):
        """Test that student can sign up for multiple activities."""
        email = "multi@mergington.edu"
        
        response1 = client.post(f"/activities/Chess Club/signup?email={email}")
        assert response1.status_code == 200
        
        response2 = client.post(f"/activities/Programming Class/signup?email={email}")
        assert response2.status_code == 200
        
        activities = client.get("/activities").json()
        assert email in activities["Chess Club"]["participants"]
        assert email in activities["Programming Class"]["participants"]

    def test_signup_increases_participant_count(self, client, reset_activities):
        """Test that signup increases participant count."""
        response = client.get("/activities")
        initial_count = len(response.json()["Basketball"]["participants"])
        
        client.post("/activities/Basketball/signup?email=newstudent@mergington.edu")
        
        response = client.get("/activities")
        new_count = len(response.json()["Basketball"]["participants"])
        assert new_count == initial_count + 1


class TestUnregisterFromActivity:
    """Tests for the POST /activities/{activity_name}/unregister endpoint."""

    def test_unregister_success(self, client, reset_activities):
        """Test successful unregistration from an activity."""
        email = "michael@mergington.edu"  # Already in Chess Club
        response = client.post(f"/activities/Chess Club/unregister?email={email}")
        assert response.status_code == 200
        assert "Unregistered" in response.json()["message"]

    def test_unregister_removes_participant(self, client, reset_activities):
        """Test that unregister actually removes a participant."""
        email = "michael@mergington.edu"
        client.post(f"/activities/Chess Club/unregister?email={email}")
        
        response = client.get("/activities")
        activities = response.json()
        assert email not in activities["Chess Club"]["participants"]

    def test_unregister_nonexistent_activity(self, client, reset_activities):
        """Test unregister from non-existent activity returns 404."""
        response = client.post(
            "/activities/Fake Activity/unregister?email=test@mergington.edu"
        )
        assert response.status_code == 404
        assert "Activity not found" in response.json()["detail"]

    def test_unregister_not_registered(self, client, reset_activities):
        """Test unregister for non-registered student returns 404."""
        response = client.post(
            "/activities/Chess Club/unregister?email=notregistered@mergington.edu"
        )
        assert response.status_code == 404
        assert "not registered" in response.json()["detail"]

    def test_unregister_decreases_participant_count(self, client, reset_activities):
        """Test that unregister decreases participant count."""
        response = client.get("/activities")
        initial_count = len(response.json()["Chess Club"]["participants"])
        
        client.post("/activities/Chess Club/unregister?email=michael@mergington.edu")
        
        response = client.get("/activities")
        new_count = len(response.json()["Chess Club"]["participants"])
        assert new_count == initial_count - 1

    def test_unregister_then_signup_again(self, client, reset_activities):
        """Test that a student can sign up again after unregistering."""
        email = "michael@mergington.edu"
        
        # Unregister
        client.post(f"/activities/Chess Club/unregister?email={email}")
        
        # Verify unregistered
        response = client.get("/activities")
        assert email not in response.json()["Chess Club"]["participants"]
        
        # Sign up again
        response = client.post(f"/activities/Chess Club/signup?email={email}")
        assert response.status_code == 200
        
        # Verify registered
        response = client.get("/activities")
        assert email in response.json()["Chess Club"]["participants"]


class TestEdgeCases:
    """Tests for edge cases and special scenarios."""

    def test_signup_case_sensitive_email(self, client, reset_activities):
        """Test that emails are case-sensitive."""
        email1 = "Student@mergington.edu"
        email2 = "student@mergington.edu"
        
        client.post(f"/activities/Chess Club/signup?email={email1}")
        response = client.post(f"/activities/Chess Club/signup?email={email2}")
        
        # Should succeed since emails are case-sensitive
        assert response.status_code == 200

    def test_activity_name_case_sensitive(self, client, reset_activities):
        """Test that activity names are case-sensitive."""
        response = client.post(
            "/activities/chess club/signup?email=test@mergington.edu"
        )
        # Should fail because activity name is case-sensitive
        assert response.status_code == 404

    def test_concurrent_signups(self, client, reset_activities):
        """Test multiple students signing up for the same activity."""
        emails = [f"student{i}@mergington.edu" for i in range(5)]
        
        for email in emails:
            response = client.post(f"/activities/Music Band/signup?email={email}")
            assert response.status_code == 200
        
        response = client.get("/activities")
        participants = response.json()["Music Band"]["participants"]
        
        for email in emails:
            assert email in participants

    def test_all_activities_accessible(self, client, reset_activities):
        """Test that all activities are accessible for signup."""
        response = client.get("/activities")
        activities_list = response.json()
        
        for activity_name in activities_list.keys():
            response = client.post(f"/activities/{activity_name}/signup?email=test{len(activity_name)}@mergington.edu")
            assert response.status_code == 200
