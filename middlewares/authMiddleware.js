const jwt = require('jsonwebtoken');

const authMiddleware = (req, res, next) => {
    const token = req.header('Authorization').replace('Bearer ', '');
    if (!token) {
        return res
            .status(401)
            .send({ error: 'Acceso denegado. No se proporcionó token.' });
    }
    try {
        const verified = jwt.verify(token, process.env.JWT_SECRET);
        req.user = verified;
        next();
    } catch (error) {
        res.status(400).send({ error: 'Token no válido' });
    }
};

module.exports = authMiddleware;
