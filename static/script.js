// Smooth scroll to sections on navigation link clicks
document.querySelectorAll('.nav-link').forEach(link => {
  link.addEventListener('click', function (e) {
    e.preventDefault();
    const targetId = this.getAttribute('href').substring(1);
    const targetElement = document.getElementById(targetId);
    if (targetElement) {
      targetElement.scrollIntoView({ behavior: 'smooth' });
    }
  });
});

// Handling contact form submission
document.querySelector('form').addEventListener('submit', function (e) {
  e.preventDefault();
  alert('Thank you for your message! We will contact you shortly.');
});

// Handling registration form submission
document.getElementById('signupForm')?.addEventListener('submit', function (e) {
  e.preventDefault(); // Prevent default behavior

  const name = document.getElementById('name').value;
  const email = document.getElementById('email').value;
  const password = document.getElementById('password').value;
  const confirmPassword = document.getElementById('confirmPassword').value;

  if (password !== confirmPassword) {
    alert('Passwords do not match!');
    return;
  }

  // Sending data to the server
  fetch('/register', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      name: name,
      email: email,
      password: password,
    }),
  })
    .then(response => {
      if (response.ok) {
        alert('Registration successful!');
        window.location.href = '/'; // Redirect to homepage
      } else {
        alert('Registration failed.');
      }
    })
    .catch(error => console.error('Error:', error));
});

// Handling login form submission
document.getElementById('loginForm')?.addEventListener('submit', function (e) {
  e.preventDefault();

  const email = document.getElementById('email').value;
  const password = document.getElementById('password').value;

  // Sending data to the server
  fetch('/login', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      email: email,
      password: password,
    }),
  })
    .then(response => {
      if (response.ok) {
        alert('Login successful!');
        window.location.href = '/dashboard'; // Redirect to dashboard
      } else {
        alert('Login failed.');
      }
    })
    .catch(error => console.error('Error:', error));
});

// Feedback form handling
document.addEventListener('DOMContentLoaded', function () {
  const feedbackForm = document.getElementById('feedbackForm');
  const feedbackAlert = document.getElementById('feedbackAlert');

  feedbackForm.addEventListener('submit', async function (event) {
    event.preventDefault(); // Prevent the default form submission

    // Get data from the form
    const formData = new FormData(feedbackForm);
    const feedbackData = {
      name: formData.get('name'),
      email: formData.get('email'),
      mark: formData.get('mark'),
      message: formData.get('message'),
    };

    try {
      // Sending data to the server using fetch
      const response = await fetch('/feedback', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(feedbackData),
      });

      if (response.ok) {
        // Clear the form after successful submission
        feedbackForm.reset();
        showFeedbackAlert('Your feedback has been successfully sent!', 'success');
      } else {
        throw new Error('Submission error. Please try again.');
      }
    } catch (error) {
      showFeedbackAlert(error.message, 'danger');
    }
  });

  // Function to display alert messages
  function showFeedbackAlert(message, type) {
    feedbackAlert.innerHTML = `<div class="alert alert-${type}" role="alert">${message}</div>`;
    setTimeout(() => {
      feedbackAlert.innerHTML = ''; // Remove alert after 5 seconds
    }, 5000);
  }
});

// all_excursion
$(document).ready(function () {
  // Initialize DataTables with sorting and English localization
  $('#excursionsTable').DataTable({
    "language": {
      "url": "//cdn.datatables.net/plug-ins/1.13.4/i18n/en-GB.json" // English localization
    }
  });

  // Add click event to rows to redirect to excursion details
  $('#excursionsTable tbody').on('click', 'tr', function () {
    const link = $(this).find('a').attr('href'); // Extract href from the link in the row
    if (link) {
      window.location.href = link; // Redirect to the details page
    }
  });
});

// excursion
$(document).ready(function () {
  // Handle "Back to All Excursions" button click
  $('#backToExcursions').on('click', function () {
    window.location.href = '/excursions'; // Redirect to the list of excursions
  });

  // Smooth scrolling for internal links (if any)
  $('a[href^="#"]').on('click', function (e) {
    e.preventDefault();
    const target = $(this.getAttribute('href'));
    if (target.length) {
      $('html, body').animate({
        scrollTop: target.offset().top
      }, 500); // Smooth scroll to the target section
    }
  });
});

// Excursion booking function
async function bookExcursion(excursionId) {
  try {
    const response = await fetch(`/book/${excursionId}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      }
    });

    if (response.ok) {
      alert("Excursion successfully booked!");
      window.location.href = "/dashboard"; // Redirect to user dashboard
    } else {
      const error = await response.json();
      alert(`Error: ${error.message}`);
    }
  } catch (error) {
    console.error('Booking error:', error);
    alert("Something went wrong. Please try again.");
  }
}

// Render excursions with booking button
function renderTrips(trips) {
  const container = document.getElementById("trips-container");
  container.innerHTML = "";

  trips.forEach(trip => {
    const tripElement = document.createElement("div");
    tripElement.className = "trip";
    tripElement.innerHTML = `
      <h3>${trip.name}</h3>
      <img src="${trip.image}" alt="${trip.name}">
      <p><strong>Location:</strong> ${trip.location}</p>
      <p><strong>Price:</strong> ${trip.price} UAH</p>
      <p><strong>Dates:</strong> ${trip.startDate} - ${trip.endDate}</p>
      <button onclick="bookExcursion(${trip.id})">Book Now</button>
    `;
    container.appendChild(tripElement);
  });
}

document.getElementById('bookButton').addEventListener('click', async function () {
  const excursionId = 3; // ID for Kyiv Tour

  try {
    const response = await fetch(`/book/${excursionId}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      }
    });

    if (response.ok) {
      const data = await response.json();
      alert(data.message); // Success message
      window.location.href = "/dashboard"; // Redirect to user dashboard
    } else if (response.status === 401) {
      alert("You are not authorized. Please log in to book the excursion.");
      window.location.href = "/login";
    } else if (response.status === 404) {
      alert("Excursion not found. Please try another one.");
    } else if (response.status === 400) {
      alert("Insufficient funds to complete the booking.");
    } else {
      alert("An unknown error occurred. Please try again later.");
    }
  } catch (error) {
    console.error('Booking error:', error);
    alert("Something went wrong. Please try again.");
  }
});