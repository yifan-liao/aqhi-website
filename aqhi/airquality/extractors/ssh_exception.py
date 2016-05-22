# Exception wrappers for paramiko.ssh_exception
class SSHException (Exception):
    """
    Exception raised by failures in SSH2 protocol negotiation or logic errors.
    """
    pass


class AuthenticationException (SSHException):
    """
    Exception raised when authentication failed for some reason.  It may be
    possible to retry with different credentials.  (Other classes specify more
    specific reasons.)
    """
    pass


class PasswordRequiredException (AuthenticationException):
    """
    Exception raised when a password is needed to unlock a private key file.
    """
    pass


class ConnectionRefued(SSHException):
    """
    Exception raised possibly when trying to log on as unknown user.
    """
    pass


class ConnectionTimeOut(SSHException):
    """
    Exception raised when connection timed out.
    """
    pass


class ServerNotKnown(SSHException):
    """
    Exception raised when connection timed out.
    """
