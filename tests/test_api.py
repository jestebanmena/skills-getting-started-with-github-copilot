"""
FastAPI Backend Tests for Mergington High School Activities API

Tests follow the AAA (Arrange-Act-Assert) pattern:
- Arrange: Set up test data and preconditions
- Act: Execute the action (make HTTP request)
- Assert: Verify response status, body, and side effects
"""

import pytest


# ============================================================================
# GET / (Static Redirect) Tests
# ============================================================================

class TestStaticRedirect:
    """Tests for the GET / endpoint."""

    def test_redirect_to_static(self, client):
        """
        Arrange: Client is ready
        Act: Make a GET request to /
        Assert: Should return 307 status and redirect to /static/index.html
        """
        # Arrange
        expected_redirect_path = "/static/index.html"

        # Act
        response = client.get("/", follow_redirects=False)

        # Assert
        assert response.status_code == 307
        assert expected_redirect_path in response.headers.get("location", "")


# ============================================================================
# GET /activities Tests
# ============================================================================

class TestGetActivities:
    """Tests for the GET /activities endpoint."""

    def test_get_all_activities(self, client):
        """
        Arrange: Client is ready with app initialized
        Act: Make a GET request to /activities
        Assert: Should return 200 with all 9 activities in response
        """
        # Arrange
        expected_activity_count = 9
        expected_activities = [
            "Chess Club",
            "Programming Class",
            "Gym Class",
            "Soccer Team",
            "Basketball Club",
            "Drama Club",
            "Art Studio",
            "Debate Team",
            "Science Club",
        ]

        # Act
        response = client.get("/activities")
        data = response.json()

        # Assert
        assert response.status_code == 200
        assert len(data) == expected_activity_count
        activity_names = list(data.keys())
        for expected_name in expected_activities:
            assert expected_name in activity_names

    @pytest.mark.parametrize(
        "activity_name",
        [
            "Chess Club",
            "Programming Class",
            "Drama Club",
        ],
    )
    def test_activity_structure(self, client, activity_name):
        """
        Arrange: Known activity names for testing
        Act: GET /activities and extract a specific activity
        Assert: Each activity should have correct structure and required fields
        """
        # Arrange
        required_fields = [
            "description",
            "schedule",
            "max_participants",
            "participants",
        ]

        # Act
        response = client.get("/activities")
        data = response.json()
        activity = data.get(activity_name)

        # Assert
        assert activity is not None, f"Activity '{activity_name}' not found"
        for field in required_fields:
            assert field in activity, f"Field '{field}' missing from activity"
        assert isinstance(activity["description"], str)
        assert isinstance(activity["schedule"], str)
        assert isinstance(activity["max_participants"], int)
        assert isinstance(activity["participants"], list)

    def test_activities_list_reflects_signup(self, client, sample_activity_name, test_email):
        """
        Arrange: Get initial activities state
        Act: Sign up a student, then GET /activities
        Assert: Participant should appear in the activity's participants list
        """
        # Arrange
        # Get initial state
        response_before = client.get("/activities")
        activities_before = response_before.json()
        activity_before = activities_before[sample_activity_name]
        initial_participants = activity_before["participants"].copy()

        # Act
        # Sign up the student
        signup_response = client.post(
            f"/activities/{sample_activity_name}/signup",
            params={"email": test_email},
        )
        # Get activities after signup
        response_after = client.get("/activities")
        activities_after = response_after.json()
        activity_after = activities_after[sample_activity_name]
        participants_after = activity_after["participants"]

        # Assert
        assert signup_response.status_code == 200
        assert test_email in participants_after
        assert len(participants_after) == len(initial_participants) + 1

    def test_activities_list_reflects_deletion(self, client, sample_activity_name, test_email):
        """
        Arrange: Sign up a student first
        Act: Delete the student, then GET /activities
        Assert: Participant should no longer appear in the activity's participants list
        """
        # Arrange
        # Sign up first
        client.post(
            f"/activities/{sample_activity_name}/signup",
            params={"email": test_email},
        )
        # Get state before deletion
        response_before = client.get("/activities")
        activities_before = response_before.json()
        activity_before = activities_before[sample_activity_name]
        participants_before = activity_before["participants"].copy()

        # Act
        # Delete the participant
        delete_response = client.delete(
            f"/activities/{sample_activity_name}/participants",
            params={"email": test_email},
        )
        # Get activities after deletion
        response_after = client.get("/activities")
        activities_after = response_after.json()
        activity_after = activities_after[sample_activity_name]
        participants_after = activity_after["participants"]

        # Assert
        assert delete_response.status_code == 200
        assert test_email not in participants_after
        assert len(participants_after) == len(participants_before) - 1


# ============================================================================
# POST /activities/{activity_name}/signup Tests
# ============================================================================

class TestSignup:
    """Tests for the POST /activities/{activity_name}/signup endpoint."""

    @pytest.mark.parametrize(
        "activity_name",
        [
            "Chess Club",
            "Programming Class",
            "Soccer Team",
        ],
    )
    def test_successful_signup(self, client, activity_name, test_email):
        """
        Arrange: Valid activity name and test email
        Act: POST request to signup endpoint
        Assert: Should return 200 and student should appear in participants list
        """
        # Arrange
        # (setup is in place)

        # Act
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": test_email},
        )
        # Verify in participant list
        activities_response = client.get("/activities")
        activity_data = activities_response.json()[activity_name]

        # Assert
        assert response.status_code == 200
        assert activity_data is not None
        assert test_email in activity_data["participants"]

    def test_duplicate_signup(self, client, sample_activity_name, test_email):
        """
        Arrange: Sign up a student once
        Act: Attempt to sign up the same student again
        Assert: Second signup should be rejected with 400 status
        """
        # Arrange
        # Sign up the first time
        response_first = client.post(
            f"/activities/{sample_activity_name}/signup",
            params={"email": test_email},
        )

        # Act
        # Attempt to sign up again
        response_second = client.post(
            f"/activities/{sample_activity_name}/signup",
            params={"email": test_email},
        )

        # Assert
        assert response_first.status_code == 200
        # Second signup should fail with 400 (student already signed up)
        assert response_second.status_code == 400

    def test_signup_nonexistent_activity(self, client, test_email):
        """
        Arrange: Invalid activity name
        Act: POST request to signup for non-existent activity
        Assert: Should return 404 error
        """
        # Arrange
        invalid_activity = "NonExistent Activity"

        # Act
        response = client.post(
            f"/activities/{invalid_activity}/signup",
            params={"email": test_email},
        )

        # Assert
        assert response.status_code == 404

    def test_signup_missing_email_parameter(self, client, sample_activity_name):
        """
        Arrange: Valid activity name but no email parameter
        Act: POST request without ?email query parameter
        Assert: Should return 422 (validation error)
        """
        # Arrange
        # (no email parameter provided)

        # Act
        response = client.post(
            f"/activities/{sample_activity_name}/signup"
        )

        # Assert
        assert response.status_code == 422

    def test_signup_empty_email_parameter(self, client, sample_activity_name):
        """
        Arrange: Valid activity name but empty email parameter
        Act: POST request with empty email query parameter
        Assert: Should return validation error or client error
        """
        # Arrange
        empty_email = ""

        # Act
        response = client.post(
            f"/activities/{sample_activity_name}/signup",
            params={"email": empty_email},
        )

        # Assert
        # Empty email might be treated as valid string or rejected
        # Actual behavior depends on app validation
        assert response.status_code in [200, 400, 422]


# ============================================================================
# DELETE /activities/{activity_name}/participants Tests
# ============================================================================

class TestParticipantRemoval:
    """Tests for the DELETE /activities/{activity_name}/participants endpoint."""

    @pytest.mark.parametrize(
        "activity_name",
        [
            "Chess Club",
            "Programming Class",
            "Basketball Club",
        ],
    )
    def test_successful_participant_removal(
        self, client, activity_name, test_email
    ):
        """
        Arrange: Sign up a student first
        Act: DELETE request to remove participant
        Assert: Should return 200 and student should no longer be in participants list
        """
        # Arrange
        # Sign up first
        client.post(
            f"/activities/{activity_name}/signup",
            params={"email": test_email},
        )

        # Act
        response = client.delete(
            f"/activities/{activity_name}/participants",
            params={"email": test_email},
        )
        # Verify removal from participant list
        activities_response = client.get("/activities")
        activity_data = activities_response.json().get(activity_name)

        # Assert
        assert response.status_code == 200
        assert activity_data is not None
        assert test_email not in activity_data["participants"]

    def test_delete_from_nonexistent_activity(self, client, test_email):
        """
        Arrange: Invalid activity name
        Act: DELETE request for non-existent activity
        Assert: Should return 404 error
        """
        # Arrange
        invalid_activity = "NonExistent Activity"

        # Act
        response = client.delete(
            f"/activities/{invalid_activity}/participants",
            params={"email": test_email},
        )

        # Assert
        assert response.status_code == 404

    def test_delete_participant_not_signed_up(
        self, client, sample_activity_name, test_email
    ):
        """
        Arrange: Activity name and email that was never signed up
        Act: DELETE request for participant not in the activity
        Assert: Should return error (400 or 404)
        """
        # Arrange
        # (email is not signed up for this activity)

        # Act
        response = client.delete(
            f"/activities/{sample_activity_name}/participants",
            params={"email": test_email},
        )

        # Assert
        assert response.status_code in [400, 404]

    def test_delete_missing_email_parameter(self, client, sample_activity_name):
        """
        Arrange: Valid activity name but no email parameter
        Act: DELETE request without ?email query parameter
        Assert: Should return 422 (validation error)
        """
        # Arrange
        # (no email parameter provided)

        # Act
        response = client.delete(
            f"/activities/{sample_activity_name}/participants"
        )

        # Assert
        assert response.status_code == 422

    def test_delete_empty_email_parameter(self, client, sample_activity_name):
        """
        Arrange: Valid activity name but empty email parameter
        Act: DELETE request with empty email query parameter
        Assert: Should return 422 or 400 (validation error)
        """
        # Arrange
        empty_email = ""

        # Act
        response = client.delete(
            f"/activities/{sample_activity_name}/participants",
            params={"email": empty_email},
        )

        # Assert
        assert response.status_code in [400, 404, 422]
