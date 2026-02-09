use pyo3::exceptions::PyValueError;
use pyo3::prelude::*;

#[pyclass]
struct VolumeCoalescer {
    current_volume: i32,
    target_volume: i32,
    has_target: bool,
    volume_step: f64,
    max_steps: i32,
}

#[pymethods]
impl VolumeCoalescer {
    #[new]
    fn new(initial_volume: i32, volume_step: f64, max_steps: i32) -> PyResult<Self> {
        if volume_step <= 0.0 {
            return Err(PyValueError::new_err("volume_step must be > 0"));
        }
        if max_steps < 1 {
            return Err(PyValueError::new_err("max_steps must be >= 1"));
        }

        Ok(Self {
            current_volume: clamp(initial_volume),
            target_volume: clamp(initial_volume),
            has_target: false,
            volume_step,
            max_steps,
        })
    }

    fn update_target(&mut self, target_volume: i32) {
        self.target_volume = clamp(target_volume);
        self.has_target = true;
    }

    fn reset_current(&mut self, current_volume: i32) {
        self.current_volume = clamp(current_volume);
    }

    fn current_volume(&self) -> i32 {
        self.current_volume
    }

    fn next_action(&mut self) -> Option<(u8, i32, i32)> {
        if !self.has_target {
            return None;
        }

        let diff = self.target_volume - self.current_volume;
        if (diff as f64).abs() < self.volume_step / 2.0 {
            self.has_target = false;
            return None;
        }

        let mut steps = ((diff.abs() as f64) / self.volume_step).round() as i32;
        if steps == 0 && diff.abs() >= 1 {
            steps = 1;
        }
        steps = steps.clamp(0, self.max_steps);
        if steps == 0 {
            self.has_target = false;
            return None;
        }

        let direction: u8 = if diff > 0 { 0 } else { 1 };
        let signed_step = if diff > 0 {
            self.volume_step
        } else {
            -self.volume_step
        };

        let estimated = (self.current_volume as f64) + (steps as f64 * signed_step);
        self.current_volume = clamp(estimated.round() as i32);

        if self.current_volume == self.target_volume {
            self.has_target = false;
        }

        Some((direction, steps, self.current_volume))
    }
}

fn clamp(v: i32) -> i32 {
    v.clamp(0, 100)
}

#[pymodule]
fn ortho_remote_rs(_py: Python<'_>, m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_class::<VolumeCoalescer>()?;
    Ok(())
}
