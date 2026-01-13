package org.laioffer.planner.user.authentication;


public class UserAlreadyExistException extends RuntimeException {


    public UserAlreadyExistException() {
        super("Username already exists");
    }
}
