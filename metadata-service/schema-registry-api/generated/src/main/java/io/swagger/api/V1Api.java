/**
 * NOTE: This class is auto generated by the swagger code generator program (3.0.33).
 * https://github.com/swagger-api/swagger-codegen Do not edit the class manually.
 */
package io.swagger.api;

import com.fasterxml.jackson.databind.ObjectMapper;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.responses.ApiResponse;
import io.swagger.v3.oas.annotations.responses.ApiResponses;
import java.util.Optional;
import javax.servlet.http.HttpServletRequest;
import javax.validation.constraints.*;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.validation.annotation.Validated;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestMethod;

@javax.annotation.Generated(
    value = "io.swagger.codegen.v3.generators.java.SpringCodegen",
    date = "2022-12-20T16:52:36.517693Z[Europe/Lisbon]")
@Validated
public interface V1Api {

  Logger log = LoggerFactory.getLogger(V1Api.class);

  default Optional<ObjectMapper> getObjectMapper() {
    return Optional.empty();
  }

  default Optional<HttpServletRequest> getRequest() {
    return Optional.empty();
  }

  default Optional<String> getAcceptHeader() {
    return getRequest().map(r -> r.getHeader("Accept"));
  }

  @Operation(
      summary = "Get the server metadata",
      description = "",
      tags = {"Server Metadata (v1)"},
      hidden = true)
  @ApiResponses(
      value = {
        @ApiResponse(
            responseCode = "500",
            description = "Error code 50001 -- Error in the backend data store ")
      })
  @RequestMapping(value = "/v1/metadata/id", method = RequestMethod.GET)
  default ResponseEntity<Void> getClusterId() {
    if (getObjectMapper().isPresent() && getAcceptHeader().isPresent()) {
    } else {
      log.warn(
          "ObjectMapper or HttpServletRequest not configured in default V1Api interface so no example is generated");
    }
    return new ResponseEntity<>(HttpStatus.NOT_IMPLEMENTED);
  }

  @Operation(
      summary = "Get Schema Registry server version",
      description = "",
      tags = {"Server Metadata (v1)"})
  @ApiResponses(
      value = {
        @ApiResponse(
            responseCode = "500",
            description = "Error code 50001 -- Error in the backend data store ")
      })
  @RequestMapping(value = "/v1/metadata/version", method = RequestMethod.GET)
  default ResponseEntity<Void> getSchemaRegistryVersion() {
    if (getObjectMapper().isPresent() && getAcceptHeader().isPresent()) {
    } else {
      log.warn(
          "ObjectMapper or HttpServletRequest not configured in default V1Api interface so no example is generated");
    }
    return new ResponseEntity<>(HttpStatus.NOT_IMPLEMENTED);
  }
}
