"""
Tests for VLAN Flask API
Run with: pytest test_app.py -v
"""
import pytest
import json
from unittest.mock import Mock, patch, MagicMock
from app import app as flask_app


@pytest.fixture
def client():
    """Create a test client for the Flask app"""
    flask_app.config['TESTING'] = True
    with flask_app.test_client() as client:
        yield client


@pytest.fixture
def mock_firebase_token():
    """Mock Firebase token verification"""
    with patch('app.auth.verify_id_token') as mock_verify:
        mock_verify.return_value = {'uid': 'test-user-123'}
        yield mock_verify


@pytest.fixture
def mock_asg_director():
    """Mock ASGDirector class"""
    with patch('app.ASGDirector') as mock_asg:
        instance = MagicMock()
        instance.getGames.return_value = {
            'minecraft': ['default', 'sf4'],
            'valheim': ['default'],
            'gmod': ['ttt']
        }
        instance.scale.return_value = {
            'ResponseMetadata': {'HTTPStatusCode': 200}
        }
        mock_asg.return_value = instance
        yield instance


class TestHealthEndpoint:
    """Tests for the health check endpoint"""

    def test_health_check(self, client):
        """Test that health check returns expected response"""
        response = client.get('/')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data == {'yay?': 'yay!'}


class TestAllGamesEndpoint:
    """Tests for the /allGames endpoint"""

    def test_all_games_success(self, client, mock_asg_director):
        """Test successful retrieval of all games"""
        response = client.get('/allGames')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'minecraft' in data
        assert 'valheim' in data
        assert 'gmod' in data
        assert data['minecraft'] == ['default', 'sf4']

    def test_all_games_error_handling(self, client):
        """Test error handling when ASGDirector fails"""
        with patch('app.ASGDirector') as mock_asg:
            mock_asg.side_effect = Exception('AWS connection error')
            response = client.get('/allGames')
            assert response.status_code == 500
            data = json.loads(response.data)
            assert data['success'] is False
            assert 'Unable to retrieve games' in data['errorMsg']
            # Should NOT expose internal error details
            assert 'AWS connection error' not in data['errorMsg']


class TestGameEndpoint:
    """Tests for the /game endpoint"""

    def test_game_start_success(self, client, mock_firebase_token, mock_asg_director):
        """Test successful game start"""
        response = client.post(
            '/game',
            headers={'Authorization': 'Bearer fake-token'},
            data=json.dumps({
                'game': 'minecraft',
                'gameType': 'default',
                'action': 'start'
            }),
            content_type='application/json'
        )
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert data['errorMsg'] is None
        mock_asg_director.scale.assert_called_once_with('minecraft', 'default', 'start')

    def test_game_stop_success(self, client, mock_firebase_token, mock_asg_director):
        """Test successful game stop"""
        response = client.post(
            '/game',
            headers={'Authorization': 'Bearer fake-token'},
            data=json.dumps({
                'game': 'valheim',
                'gameType': 'default',
                'action': 'stop'
            }),
            content_type='application/json'
        )
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        mock_asg_director.scale.assert_called_once_with('valheim', 'default', 'stop')

    def test_game_missing_authorization(self, client, mock_asg_director):
        """Test request without Authorization header"""
        response = client.post(
            '/game',
            data=json.dumps({
                'game': 'minecraft',
                'gameType': 'default',
                'action': 'start'
            }),
            content_type='application/json'
        )
        assert response.status_code == 401
        assert response.data == b'Unauthorized'

    def test_game_invalid_token(self, client, mock_asg_director):
        """Test request with invalid Firebase token"""
        with patch('app.auth.verify_id_token') as mock_verify:
            from firebase_admin import auth
            mock_verify.side_effect = auth.InvalidIdTokenError('Invalid token')

            response = client.post(
                '/game',
                headers={'Authorization': 'Bearer invalid-token'},
                data=json.dumps({
                    'game': 'minecraft',
                    'gameType': 'default',
                    'action': 'start'
                }),
                content_type='application/json'
            )
            assert response.status_code == 401
            data = json.loads(response.data)
            assert data['success'] is False
            assert 'Invalid authentication token' in data['errorMsg']

    def test_game_missing_parameters(self, client, mock_firebase_token, mock_asg_director):
        """Test request with missing required parameters"""
        # Missing 'action'
        response = client.post(
            '/game',
            headers={'Authorization': 'Bearer fake-token'},
            data=json.dumps({
                'game': 'minecraft',
                'gameType': 'default'
            }),
            content_type='application/json'
        )
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['success'] is False
        assert 'Missing required parameters' in data['errorMsg']

    def test_game_empty_body(self, client, mock_firebase_token, mock_asg_director):
        """Test request with empty JSON body"""
        response = client.post(
            '/game',
            headers={'Authorization': 'Bearer fake-token'},
            data=json.dumps({}),
            content_type='application/json'
        )
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['success'] is False
        assert 'Missing required parameters' in data['errorMsg']

    def test_game_invalid_action(self, client, mock_firebase_token, mock_asg_director):
        """Test request with invalid action value"""
        response = client.post(
            '/game',
            headers={'Authorization': 'Bearer fake-token'},
            data=json.dumps({
                'game': 'minecraft',
                'gameType': 'default',
                'action': 'restart'  # Invalid action
            }),
            content_type='application/json'
        )
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['success'] is False
        assert 'Invalid action' in data['errorMsg']

    def test_game_invalid_game_name(self, client, mock_firebase_token, mock_asg_director):
        """Test request with non-existent game name"""
        response = client.post(
            '/game',
            headers={'Authorization': 'Bearer fake-token'},
            data=json.dumps({
                'game': 'nonexistent-game',
                'gameType': 'default',
                'action': 'start'
            }),
            content_type='application/json'
        )
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['success'] is False
        assert 'Invalid game specified' in data['errorMsg']

    def test_game_invalid_game_type(self, client, mock_firebase_token, mock_asg_director):
        """Test request with invalid gameType for valid game"""
        response = client.post(
            '/game',
            headers={'Authorization': 'Bearer fake-token'},
            data=json.dumps({
                'game': 'minecraft',
                'gameType': 'nonexistent-type',
                'action': 'start'
            }),
            content_type='application/json'
        )
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['success'] is False
        assert 'Invalid gameType' in data['errorMsg']

    def test_game_aws_error(self, client, mock_firebase_token, mock_asg_director):
        """Test handling of AWS errors"""
        mock_asg_director.scale.return_value = {
            'ResponseMetadata': {'HTTPStatusCode': 500}
        }

        response = client.post(
            '/game',
            headers={'Authorization': 'Bearer fake-token'},
            data=json.dumps({
                'game': 'minecraft',
                'gameType': 'default',
                'action': 'start'
            }),
            content_type='application/json'
        )
        assert response.status_code == 500
        data = json.loads(response.data)
        assert data['success'] is False
        assert data['errorMsg'] == 'AWS Problems'

    def test_game_exception_no_info_disclosure(self, client, mock_firebase_token, mock_asg_director):
        """Test that internal exceptions don't leak sensitive information"""
        mock_asg_director.scale.side_effect = Exception('Internal AWS error: secret-key-12345')

        response = client.post(
            '/game',
            headers={'Authorization': 'Bearer fake-token'},
            data=json.dumps({
                'game': 'minecraft',
                'gameType': 'default',
                'action': 'start'
            }),
            content_type='application/json'
        )
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['success'] is False
        # Generic error message
        assert 'An error occurred processing your request' in data['errorMsg']
        # Should NOT contain internal error details
        assert 'secret-key-12345' not in data['errorMsg']
        assert 'Internal AWS error' not in data['errorMsg']


class TestSecurityValidation:
    """Tests specifically for security vulnerability fixes"""

    def test_sql_injection_attempt(self, client, mock_firebase_token, mock_asg_director):
        """Test that SQL-like injection attempts are blocked"""
        response = client.post(
            '/game',
            headers={'Authorization': 'Bearer fake-token'},
            data=json.dumps({
                'game': "minecraft'; DROP TABLE games; --",
                'gameType': 'default',
                'action': 'start'
            }),
            content_type='application/json'
        )
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['success'] is False
        # Should fail validation before reaching ASG
        mock_asg_director.scale.assert_not_called()

    def test_path_traversal_attempt(self, client, mock_firebase_token, mock_asg_director):
        """Test that path traversal attempts are blocked"""
        response = client.post(
            '/game',
            headers={'Authorization': 'Bearer fake-token'},
            data=json.dumps({
                'game': '../../../etc/passwd',
                'gameType': 'default',
                'action': 'start'
            }),
            content_type='application/json'
        )
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['success'] is False
        mock_asg_director.scale.assert_not_called()

    def test_no_exception_details_in_error(self, client, mock_firebase_token, mock_asg_director):
        """Verify exception details are never exposed to client"""
        # Test various exception types
        exceptions_to_test = [
            KeyError('secret_key'),
            ValueError('Invalid configuration value: admin_password=secret123'),
            Exception('Database connection failed: host=internal-db.company.com'),
        ]

        for exc in exceptions_to_test:
            mock_asg_director.scale.side_effect = exc

            response = client.post(
                '/game',
                headers={'Authorization': 'Bearer fake-token'},
                data=json.dumps({
                    'game': 'minecraft',
                    'gameType': 'default',
                    'action': 'start'
                }),
                content_type='application/json'
            )

            data = json.loads(response.data)
            # Should only contain generic error message
            assert data['errorMsg'] == 'An error occurred processing your request'
            # Should not contain any part of the exception message
            assert 'secret' not in data['errorMsg'].lower()
            assert 'password' not in data['errorMsg'].lower()
            assert 'internal-db' not in data['errorMsg'].lower()


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
